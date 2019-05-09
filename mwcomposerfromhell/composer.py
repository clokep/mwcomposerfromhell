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

# The markup for different lists mapped to the list tag and list item tag.
MARKUP_TO_LIST = {
    '*': ('ul', 'li'),
    '#': ('ol', 'li'),
    ';': ('dl', 'dt'),
}


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

        self._pending_lists = []

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

    def clone(self, context):
        """Create a copy of this WikicodeToHtmlComposer."""
        return WikicodeToHtmlComposer(
            self._base_url,
            template_store=self._template_store,
            context=context)

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
        # List tags require a parent tag to be open first, but get grouped
        # if one is already open.
        if node.wiki_markup in MARKUP_TO_LIST:
            list_tag, item_tag = MARKUP_TO_LIST[node.wiki_markup]
            # Mark that this tag needs to be opened.
            self._pending_lists.append((list_tag, item_tag))

            # ul and ol cannot be inside of a dl and a dl cannot be in a ul or
            # ol.
            if node.wiki_markup in ('*', '#'):
                self._close_stack('dl', raise_on_missing=False)
            else:
                self._close_stack('ol', raise_on_missing=False)
                self._close_stack('ul', raise_on_missing=False)

        else:
            composer = self.clone(self._context)
            composer.visit(node.tag)
            tag = composer.stream.getvalue().strip()

            # Create an HTML tag.
            self.write('<{}'.format(tag))
            for attr in node.attributes:
                self.visit(attr)
            self.write('>')
            self._stack.append(tag)

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

        LIST_TAGS = {'ul', 'ol', 'dl'}
        TAGS_TO_CLOSE = LIST_TAGS.copy() | {'li', 'dt'}

        if self._pending_lists:
            stack_lists = [list_node for list_node in self._stack if list_node in LIST_TAGS]

            # Remove the prefixed part of the lists that match.
            i = 0
            shortest = min([len(stack_lists), len(self._pending_lists)])
            for i in range(shortest):
                # Each element of _pending_lists is a tuple of (list tag, item tag).
                if stack_lists[i] != self._pending_lists[i][0]:
                    break
            else:
                i = shortest

            # Now close anything left in stack_lists.
            for stack_node in reversed(stack_lists[i:]):
                self._close_stack(stack_node)

            # Re-open anything that is pending..
            for list_tag, item_tag in self._pending_lists[i:]:
                self._stack.append(list_tag)
                self.write('<{}>'.format(list_tag))

            # For the last pending list, also open the list item.
            item_tag = self._pending_lists[-1][1]
            self.write('<{}>'.format(item_tag))
            self._stack.append(item_tag)

            # Reset the list.
            self._pending_lists = []

        self.write(node.value)

        # Certain tags get closed when there's a line break.
        num_new_lines = len(node.value) - len(node.value.rstrip('\n'))

        for i in range(num_new_lines):
            # Since _close_stack mutates the _stack, check on each iteration if
            # _stack is still truth-y.
            if not self._stack:
                break

            # Close an element in the stack.
            if self._stack[-1] in TAGS_TO_CLOSE:
                self._close_stack(self._stack[-1])

    def visit_Template(self, node):
        # Render the key into a string. This handles weird cases of like
        # {{f{{text|oo}}bar}}.
        composer = self.clone(self._context)
        composer.visit(node.name)
        template_name = composer.stream.getvalue().strip()

        # Because each parameter's name and value might have other templates,
        # etc. in it we need to render those in the context of the template
        # call.
        context = OrderedDict()
        for param in node.params:
            # See https://meta.wikimedia.org/wiki/Help:Template#Parameters
            # for information about striping whitespace around parameters.
            composer = self.clone(self._context)
            composer.visit(param.name)
            param_name = composer.stream.getvalue().strip()

            composer = self.clone(self._context)
            composer.visit(param.value)
            param_value = composer.stream.getvalue()

            # Only named parameters strip whitespace aroudn the value.
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

        # Otherwise, this is a normal template.
        else:
            try:
                template = self._template_store[template_name]
            except KeyError:
                # Template was not found, simply output the template call.
                self.write(str(node))
            else:
                # Render the template in only the context of its parameters.
                composer = self.clone(context)
                composer.visit(template)
                self.write(composer.stream.getvalue())

    def visit_Argument(self, node):
        # There's no provided values, so just render the string.
        # Templates have special handling for Arguments.
        composer = self.clone(self._context)
        composer.visit(node.name)
        param_name = composer.stream.getvalue().strip()

        # Get the parameter's value from the context (the call to the
        # template we're rendering).
        try:
            self.write(self._context[param_name])
        except KeyError:
            # No parameter with this name was given.

            # Use a default value if it exists, otherwise just render the
            # parameter as a string.
            if node.default is not None:
                # Render the default value in a clean context. You cannot use
                # other parameters as defaults, see
                # https://en.wikipedia.org/wiki/Help:Template#Handling_parameters
                composer = self.clone(None)
                composer.visit(node.default)
                self.write(composer.stream.getvalue())

            else:
                self.write(str(node))

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
