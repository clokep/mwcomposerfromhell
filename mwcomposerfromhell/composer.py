from collections import OrderedDict
from io import StringIO
from urllib.parse import quote as url_quote

from mwparserfromhell.definitions import MARKUP_TO_HTML

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


class WikiNodeVisitor:
    def visit(self, node):
        method_name = 'visit_' + node.__class__.__name__

        try:
            method = getattr(self, method_name)
        except AttributeError:
            raise UnknownNode('Unknown node type: {}'.format(node.__class__.__name__))

        method(node)


class WikicodeToHtmlComposer(WikiNodeVisitor):
    """
    Format HTML from parsed Wikicode.

    Note that this is not currently re-usable.

    See https://en.wikipedia.org/wiki/Help:Wikitext for a full definition.
    """
    def __init__(self, base_url='https://en.wikipedia.org/wiki', stream=None, template_store=None, context=None):
        # The output stream.
        # TODO Accept this as an input parameter (e.g. to stream to a file).
        if stream is None:
            self.stream = StringIO()
        else:
            self.stream = stream

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

    def write(self, x):
        """Write a string into the output stream."""
        self.stream.write(x)

    def _close_stack(self, tag=None, raise_on_missing=True):
        """Close tags that are on the stack. It closes all tags until ``tag`` is found.

        If no tag to close is given the entire stack is closed.
        """
        # Close the entire stack.
        if tag is None:
            for current_tag in reversed(self._stack):
                self.write('</{}>'.format(current_tag))
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
            self.write('</{}>'.format(current_tag))

            if current_tag == tag:
                break

    def visit_Wikicode(self, node):
        for node in node.ifilter(recursive=False):
            self.visit(node)

    def visit_Tag(self, node):
        # Some tags require a parent tag to be open first, but get grouped
        # if one is already open.
        if node.wiki_markup == '*':
            self._wanted_lists.append('ul')
            # Don't allow a ul inside of a dl.
            self._close_stack('dl', raise_on_missing=False)
        elif node.wiki_markup == '#':
            self._wanted_lists.append('ol')
            # Don't allow a ul inside of a dl.
            self._close_stack('dl', raise_on_missing=False)
        elif node.wiki_markup == ';':
            self._wanted_lists.append('dl')
            # Don't allow dl instead ol or ul.
            self._close_stack('ol', raise_on_missing=False)
            self._close_stack('ul', raise_on_missing=False)

        else:
            # Create an HTML tag.
            self.write('<{}'.format(node.tag))
            for attr in node.attributes:
                self.visit(attr)
            self.write('>')
            self._stack.append(node.tag)

        # Handle anything inside of the tag.
        if node.contents:
            self.visit(node.contents)

        # Self closing tags don't need an end tag, this produces "broken"
        # HTML, but readers should handle it fine.
        if not node.self_closing:
            # Close this tag and any other open tags after it.
            self._close_stack(node.tag)

    def visit_Attribute(self, attr):
        # Just use the string version of the attribute, it does all the parsing
        # that we want.
        self.write(str(attr))

    def visit_Heading(self, node):
        self.write('<h{}>'.format(node.level))
        self.visit(node.title)
        self.write('</h{}>'.format(node.level))

    def visit_Wikilink(self, node):
        # Display text can be specified, if it is not given, fall back to the
        # article title.
        text = node.text or node.title
        url = get_article_url(self._base_url, node.title)
        self.write('<a href="{}">'.format(url))
        self.visit(text)
        self.write('</a>')

    def visit_ExternalLink(self, node):
        # Display text can be specified, if it is not given, fall back to the
        # raw URL.
        text = node.title or node.url
        self.write('<a href="{}">'.format(node.url))
        self.visit(text)
        self.write('</a>')

    def visit_Comment(self, node):
        self.write('<!-- {} -->'.format(node.contents))

    def visit_Text(self, node):
        # Write an actual text element. This needs to handle whether there's any
        # lists to open.

        if self._wanted_lists:
            stack_lists = [list_node for list_node in self._stack if list_node in ['ul', 'ol', 'dl']]

            # Remove the prefixed part of the lists that match.
            i = 0
            shortest = min([len(stack_lists), len(self._wanted_lists)])
            for i in range(shortest):
                if stack_lists[i] != self._wanted_lists[i]:
                    break
            else:
                i = shortest

            # Now close anything left in stack_lists.
            for stack_node in reversed(stack_lists[i:]):
                self._close_stack(stack_node)

            # Open anything in wanted_lists.
            for stack_node in self._wanted_lists[i:]:
                self._stack.append(stack_node)
                self.write('<{}>'.format(stack_node))

            # Finally, open the list item.
            if self._wanted_lists[-1] == 'dl':
                item_tag = 'dt'
            else:
                item_tag = 'li'
            self._stack.append(item_tag)
            self.write('<{}>'.format(item_tag))

            # Reset the list.
            self._wanted_lists = []

        self.write(node.value)

        # Certain tags get closed when there's a line break.
        num_new_lines = len(node.value) - len(node.value.rstrip('\n'))

        ELEMENTS_TO_CLOSE = ['li', 'ul', 'ol', 'dl', 'dt']

        for i in range(num_new_lines):
            # Since _close_stack mutates the _stack, check on each iteration if
            # _stack is still truth-y.
            if not self._stack:
                break

            # Close an element in the stack.
            if self._stack[-1] in ELEMENTS_TO_CLOSE:
                self._close_stack(self._stack[-1])

    def visit_Template(self, node):
        # Render the key into a string. This handles weird cases of like
        # {{f{{text|oo}}bar}}.
        composer = WikicodeToHtmlComposer(
            self._base_url, template_store=self._template_store, context=self._context)
        composer.visit(node.name)
        template_name = composer.stream.getvalue().strip()

        # Because each parameter's name and value might have other
        # templates, etc. in it we need to render those in the context of
        # the template call.
        context = OrderedDict()
        for param in node.params:
            # See https://meta.wikimedia.org/wiki/Help:Template#Parameters
            # for information about striping whitespace around parameters.
            composer = WikicodeToHtmlComposer(
                self._base_url, template_store=self._template_store, context=self._context)
            composer.visit(param.name)
            param_name = composer.stream.getvalue().strip()

            composer = WikicodeToHtmlComposer(
                self._base_url, template_store=self._template_store, context=self._context)
            composer.visit(param.value)
            param_value = composer.stream.getvalue()

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
                self.write(str(node))
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

                self.write(function(function_context))
        else:
            try:
                template = self._template_store[template_name]
            except KeyError:
                # TODO
                self.write(str(node))
            else:
                # Create a new composer with the call to include the template as the context.
                composer = WikicodeToHtmlComposer(
                    self._base_url, stream=self.stream, template_store=self._template_store, context=context)
                composer.visit(template)

    def visit_Argument(self, node):
        # There's no provided values, so just render the string.
        # Templates have special handling for Arguments.
        composer = WikicodeToHtmlComposer(
            self._base_url, template_store=self._template_store, context=self._context)
        composer.visit(node.name)
        param_name = composer.stream.getvalue().strip()

        # Get the parameter's value from the context (the call to the
        # template we're rendering).
        try:
            self.write(self._context[param_name])
        except KeyError:
            # If no parameter with this name was given. If there's a default
            # value, use it, otherwise just render the parameter as a
            # string.
            if node.default is None:
                self.write(str(node))
            else:
                composer = WikicodeToHtmlComposer(
                    self._base_url, stream=self.stream, template_store=self._template_store)
                composer.visit(node.default)

    def visit_HTMLEntity(self, node):
        # Just write the original HTML entitiy.
        self.write(str(node))

    # The following aren't nodes, but they allow some generic Python iterables
    # to be used.

    def visit_list(self, node):
        # If the object is iterable, just handle each item separately.
        for node in node:
            self.visit(node)

    visit_tuple = visit_list

    def compose(self, node):
        """Converts Wikicode or Node objects to HTML."""
        self.visit(node)
        # Ensure the stack is closed at the end.
        self._close_stack()
