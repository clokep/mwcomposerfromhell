from urllib.parse import quote as url_quote
import re

from mwparserfromhell.definitions import MARKUP_TO_HTML
from mwparserfromhell.nodes import Argument, Comment, ExternalLink, HTMLEntity, Tag, Template, Text, Wikilink
from mwparserfromhell.wikicode import Wikicode


# The MARKUP_TO_HTML is missing a few things...this duck punches them in.
MARKUP_TO_HTML.update({
    "''": 'i',
})


class UnknownNode(Exception):
    pass


class HtmlComposingError(Exception):
    pass


class WikicodeToHtmlComposer:
    """
    Format HTML from Parsed Wikicode.

    Note that this is not currently re-usable.

    https://en.wikipedia.org/wiki/Help:Wiki_markup
    """
    def __init__(self, base_url='https://en.wikipedia.org/wiki', context=None):
        # The base URL should be the root that articles sit in.
        self._base_url = base_url.rstrip('/')

        self._wanted_lists = []

        # Track the currently open tags.
        self._stack = []

        self._context = context

        # A place to cache templates.
        self._template_cache = {}

    def _get_url(self, title):
        """Given a page title, return a URL suitable for linking."""
        safe_title = url_quote(title.encode('utf-8'))
        return '{}/{}'.format(self._base_url, safe_title)

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
            url = self._get_url(obj.title)
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
            composer = WikicodeToHtmlComposer(self._base_url, context=self._context)
            # TODO This is weird.
            composer._template_cache = self._template_cache
            key = composer.compose(obj.name)

            # This represents a script, see https://www.mediawiki.org/wiki/Extension:Scribunto
            if key.startswith('#'):
                yield from self._add_part(str(obj))

            try:
                template = self._template_cache[key]
            except KeyError:
                # Get the template from the server.
                template_str = get_article(get_article_url('Template:' + key))

                # Only use the parts that would be included.
                pat = re.compile(r'<noinclude>.*?</noinclude>', flags=re.DOTALL)
                template_str = pat.sub(r'', template_str)
                pat = re.compile(r'<includeonly>(.*?)</includeonly>', flags=re.DOTALL)
                template_str = pat.sub(r'\1', template_str)

                # Parse the template to Wikicode
                template = mwparserfromhell.parse(template_str)

                # Store it for subsequent calls.
                self._template_cache[key] = template

            # Create a new composer with the call to include the template as the context.
            composer = WikicodeToHtmlComposer(self._base_url, context=obj)
            yield composer.compose(template)

        elif isinstance(obj, Argument):
            # There's no provided values, so just render the string.
            # Templates have special handling for Arguments.
            param_name = str(obj.name)
            try:
                param = self._context.get(param_name)
                yield str(param.value)
            except (AttributeError, ValueError):
                if obj.default is None:
                    yield from self._add_part(str(obj))
                else:
                    yield str(obj.default)

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
