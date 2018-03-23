from collections import OrderedDict
from urllib.parse import quote as url_quote

from mwparserfromhell.definitions import MARKUP_TO_HTML
from mwparserfromhell.nodes import Argument, Comment, ExternalLink, HTMLEntity, Tag, Template, Text, Wikilink
from mwparserfromhell.wikicode import Wikicode

from mwcomposerfromhell.modules import ModuleStore, UnknownModule
from mwcomposerfromhell.templates import TemplateStore

# The MARKUP_TO_HTML is missing a few things...this duck punches them in.
MARKUP_TO_HTML.update({
    "''": 'i',
})


class UnknownNode(Exception):
    pass


class HtmlComposingError(Exception):
    pass


def get_article_url(base_url, title):
    """Given a page title, return a URL suitable for linking."""
    safe_title = url_quote(title.encode('utf-8'))
    return '{}/{}'.format(base_url, safe_title)


class WikicodeToHtmlComposer:
    """
    Format HTML from parsed Wikicode.

    Note that this is not currently re-usable.

    See https://en.wikipedia.org/wiki/Help:Wikitext for a full definition.
    """
    def __init__(self, base_url='https://en.wikipedia.org/wiki', template_store=None, context=None):
        # The base URL should be the root that articles sit in.
        self._base_url = base_url.rstrip('/')

        self._wanted_lists = []

        # Track the currently open tags.
        self._stack = []

        self._context = context

        # A place to lookup templates.
        if template_store is None:
            template_store = TemplateStore()
        elif isinstance(template_store, dict):
            template_store = TemplateStore(template_store)
        elif not isinstance(template_store, TemplateStore):
            raise ValueError('template_store must be an instance of TemplateStore')
        self._template_store = template_store

        # A place to lookup modules.
        self._module_store = ModuleStore()

    def _close_stack(self, tag=None, raise_on_missing=True):
        """Close tags that are on the stack. It closes all tags until ``tag`` is found.

        If no tag to close is given the entire stack is closed.
        """
        # Close the entire stack.
        if tag is None:
            for current_tag in reversed(self._stack):
                yield u'</{}>'.format(current_tag)
            return

        # If a tag was given, close all tags behind it (in reverse order).
        if tag not in self._stack:
            # TODO
            if raise_on_missing:
                raise HtmlComposingError('Unable to close given tags.')
            else:
                return

        while len(self._stack):
            current_tag = self._stack.pop()
            yield u'</{}>'.format(current_tag)

            if current_tag == tag:
                break

    def _add_part(self, part):
        """Append a part, closing any parts of the stack that should be closed here."""
        if self._wanted_lists:
            stack_lists = [node for node in self._stack if node in ['ul', 'ol', 'dl']]

            # Remove the prefixed part of the lists that match.
            i = 0
            shortest = min([len(stack_lists), len(self._wanted_lists)])
            for i in range(shortest):
                if stack_lists[i] != self._wanted_lists[i]:
                    break
            else:
                i = shortest

            # Now close anything left in stack_lists.
            for node in reversed(stack_lists[i:]):
                yield from self._close_stack(node)

            # Open anything in wanted_lists.
            for node in self._wanted_lists[i:]:
                self._stack.append(node)
                yield u'<{}>'.format(node)

            # Finally, open the list item.
            if self._wanted_lists[-1] == 'dl':
                item_tag = 'dt'
            else:
                item_tag = 'li'
            self._stack.append(item_tag)
            yield u'<{}>'.format(item_tag)

            # Reset the list.
            self._wanted_lists = []

        yield part

        # Certain tags get closed when there's a line break.
        for c in reversed(part):
            # Since _close_stack mutates the _stack, check on each iteration if
            # _stack is still truth-y.
            if not self._stack:
                break

            if c == '\n':
                elements_to_close = ['li', 'ul', 'ol', 'dl', 'dt']
                # Close an element in the stack.
                if self._stack[-1] in elements_to_close:
                    yield from self._close_stack(self._stack[-1])
            else:
                break

    def _compose_parts(self, obj):
        """Takes an object and returns a generator that will compose one more pieces of HTML."""
        if isinstance(obj, Wikicode):
            for node in obj.ifilter(recursive=False):
                yield from self._compose_parts(node)

        elif isinstance(obj, Tag):
            # Some tags require a parent tag to be open first, but get grouped
            # if one is already open.
            if obj.wiki_markup == '*':
                self._wanted_lists.append('ul')
                # Don't allow a ul inside of a dl.
                yield from self._close_stack('dl', raise_on_missing=False)
            elif obj.wiki_markup == '#':
                self._wanted_lists.append('ol')
                # Don't allow a ul inside of a dl.
                yield from self._close_stack('dl', raise_on_missing=False)
            elif obj.wiki_markup == ';':
                self._wanted_lists.append('dl')
                # Don't allow dl instead ol or ul.
                yield from self._close_stack('ol', raise_on_missing=False)
                yield from self._close_stack('ul', raise_on_missing=False)

            else:
                # Create an HTML tag.
                # TODO Handle attributes.
                yield from self._add_part(u'<{}>'.format(obj.tag))
                self._stack.append(obj.tag)

            for child in obj.__children__():
                yield from self._compose_parts(child)

            # Self closing tags don't need an end tag, this produces "broken"
            # HTML, but readers should handle it fine.
            if not obj.self_closing:
                # Close this tag and any other open tags after it.
                yield from self._close_stack(obj.tag)

        elif isinstance(obj, Wikilink):
            # Different text can be specified, or falls back to the title.
            text = obj.text or obj.title
            url = get_article_url(self._base_url, obj.title)
            yield from self._add_part(u'<a href="{}">'.format(url))
            yield from self._compose_parts(text)
            yield from self._add_part(u'</a>')

        elif isinstance(obj, ExternalLink):
            # Different text can be specified, or falls back to the URL.
            text = obj.title or obj.url
            yield from self._add_part(u'<a href="{}">'.format(obj.url))
            yield from self._compose_parts(text)
            yield from self._add_part(u'</a>')

        elif isinstance(obj, Comment):
            yield from self._add_part(u'<!-- {} -->'.format(obj.contents))

        elif isinstance(obj, Text):
            yield from self._add_part(obj.value)

        elif isinstance(obj, Template):
            # Render the key into a string. This handles weird cases of like
            # {{f{{text|oo}}bar}}.
            composer = WikicodeToHtmlComposer(
                self._base_url, template_store=self._template_store, context=self._context)
            template_name = composer.compose(obj.name).strip()

            # Because each parameter's name and value might have other
            # templates, etc. in it we need to render those in the context of
            # the template call.
            context = OrderedDict()
            for param in obj.params:
                # See https://meta.wikimedia.org/wiki/Help:Template#Parameters
                # for information about striping whitespace around parameters.
                composer = WikicodeToHtmlComposer(
                    self._base_url, template_store=self._template_store, context=self._context)
                param_name = composer.compose(param.name).strip()

                composer = WikicodeToHtmlComposer(
                    self._base_url, template_store=self._template_store, context=self._context)
                param_value = composer.compose(param.value)

                # Only named parameters get whitespace striped.
                if param.showkey:
                    param_value = param_value.strip()

                context[param_name] = param_value

            # This represents a script, see https://www.mediawiki.org/wiki/Extension:Scribunto
            if template_name.startswith('#invoke:'):
                template_name, _, module_name = template_name.partition(':')

                try:
                    # Get the function names from the parameters.
                    _, function_name = context.popitem(last=False)

                    # Get the actual function.
                    function = self._module_store.get_function(module_name, function_name)
                except UnknownModule:
                    # TODO
                    yield from self._add_part(str(obj))
                else:
                    # Call the script with the provided context. Note that we
                    # can't do anything fancy with the parameters because
                    # MediaWiki lets you have non-named parameters after named
                    # parameters. We do need to re-number them, however, so that
                    # they begin at '1' and not '2'.
                    function_context = OrderedDict()
                    for key, value in context.items():
                        try:
                            key = int(key)
                        except ValueError:
                            pass
                        else:
                            key -= 1
                        finally:
                            function_context[str(key)] = value

                    yield function(function_context)
            else:
                try:
                    template = self._template_store[template_name]
                except KeyError:
                    # TODO
                    yield from self._add_part(str(obj))
                else:
                    # Create a new composer with the call to include the template as the context.
                    composer = WikicodeToHtmlComposer(
                        self._base_url, template_store=self._template_store, context=context)
                    yield composer.compose(template)

        elif isinstance(obj, Argument):
            # There's no provided values, so just render the string.
            # Templates have special handling for Arguments.
            composer = WikicodeToHtmlComposer(
                self._base_url, template_store=self._template_store, context=self._context)
            param_name = composer.compose(obj.name).strip()

            # Get the parameter's value from the context (the call to the
            # template we're rendering).
            try:
                value = self._context[param_name]
            except KeyError:
                # If no parameter with this name was given. If there's a default
                # value, use it, otherwise just render the parameter as a
                # string.
                if obj.default is None:
                    value = str(obj)
                else:
                    composer = WikicodeToHtmlComposer(
                        self._base_url, template_store=self._template_store)
                    value = composer.compose(obj.default)

            yield value

        elif isinstance(obj, HTMLEntity):
            # TODO
            yield from self._add_part(str(obj))

        elif isinstance(obj, (list, tuple)):
            # If the object is iterable, just handle each item separately.
            for node in obj:
                yield from self._compose_parts(node)

        else:
            raise UnknownNode(u'Unknown node type: {}'.format(type(obj)))

    def compose(self, obj):
        """Converts Wikicode or Node objects to HTML."""
        # TODO Add a guard that this can only be called once at a time.

        return u''.join(self._compose_parts(obj)) + u''.join(self._close_stack())
