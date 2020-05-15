from collections import OrderedDict
import html
from typing import Dict, List, Optional
from urllib.parse import quote as url_quote

from mwcomposerfromhell.modules import ModuleStore, UnknownModule
from mwcomposerfromhell.templates import TemplateStore

# The markup for different lists mapped to the list tag and list item tag.
MARKUP_TO_LIST = {
    '*': ('ul', 'li'),
    '#': ('ol', 'li'),
    ';': ('dl', 'dt'),
}

# The markup for tags which are inline, as opposed to block.
INLINE_TAGS = {"''", "'''"}

# The type for a Template Context.
TemplateContext = Dict[str, str]


class UnknownNode(Exception):
    pass


class HtmlComposingError(Exception):
    pass


def get_article_url(base_url: str, title: str) -> str:
    """Given a page title, return a URL suitable for linking."""
    safe_title = url_quote(title.encode('utf-8'))
    return '{}/{}'.format(base_url, safe_title)


class WikiNodeVisitor:
    def visit(self, node, in_root=False):
        method_name = 'visit_' + node.__class__.__name__

        try:
            method = getattr(self, method_name)
        except AttributeError:
            raise UnknownNode('Unknown node type: {}'.format(node.__class__.__name__))

        return method(node, in_root)


class WikicodeToHtmlComposer(WikiNodeVisitor):
    """
    Format HTML from parsed Wikicode.

    Note that this is not currently re-usable.

    See https://en.wikipedia.org/wiki/Help:Wikitext for a full definition.
    """
    def __init__(self,
                 base_url: str = 'https://en.wikipedia.org/wiki',
                 template_store: Optional[TemplateStore] = None,
                 context: Optional[TemplateContext] = None):

        # The base URL should be the root that articles sit in.
        self._base_url = base_url.rstrip('/')

        self._pending_lists: List[str] = []

        # Track the currently open tags.
        self._stack: List[str] = []

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

    def _maybe_open_paragraph(self, in_root):
        """
        Handle the logic for whether this node gets wrapped in a paragraph.

        This only happens if:

        1. The node is in the "root" Wikicode.
        2. There's nothing on the stack.
        """
        if not in_root or self._stack:
            return ''

        self._stack.append('p')
        return '<p>'

    def _close_stack(self, tag: str):
        """Close tags that are on the stack. It closes all tags until ``tag`` is found."""
        # For the given tag, close all tags behind it (in reverse order).
        result = ''
        while len(self._stack):
            current_tag = self._stack.pop()
            result += '</{}>'.format(current_tag)

            if current_tag == tag:
                break

        return result

    def visit_Wikicode(self, node, in_root=False):
        return ''.join(map(lambda n: self.visit(n, in_root), node.nodes))

    def visit_Tag(self, node, in_root=False):
        result = ''

        # List tags require a parent tag to be opened first, but get grouped
        # together if one is already open.
        if node.wiki_markup in MARKUP_TO_LIST:
            list_tag, item_tag = MARKUP_TO_LIST[node.wiki_markup]
            # Mark that this tag needs to be opened.
            self._pending_lists.append((list_tag, item_tag))

            # ul and ol cannot be inside of a dl and a dl cannot be in a ul or
            # ol.
            if node.wiki_markup in ('*', '#'):
                if 'dl' in self._stack:
                    result += self._close_stack('dl')
            else:
                if 'ol' in self._stack:
                    result += self._close_stack('ol')
                if 'ul' in self._stack:
                    result += self._close_stack('ul')

        else:
            tag = self.visit(node.tag)

            # Maybe wrap the tag in a paragraph, notably this gets ignored for
            # tables and some other tags.
            if node.wiki_markup in INLINE_TAGS:
                result += self._maybe_open_paragraph(in_root)

            # Create an HTML tag.
            result += '<' + tag
            for attr in node.attributes:
                result += self.visit(attr)
            result += '>'
            self._stack.append(tag)

        # Handle anything inside of the tag.
        if node.contents:
            result += self.visit(node.contents)

        # Self closing tags don't need an end tag, this produces "broken"
        # HTML, but readers should handle it fine.
        if not node.self_closing:
            # Close this tag and any other open tags after it.
            result += self._close_stack(node.tag)

        return result

    def visit_Attribute(self, node, in_root=False):
        # Just use the string version of the attribute, it does all the parsing
        # that we want.
        return str(node)

    def visit_Heading(self, node, in_root=False):
        return '<h{}>'.format(node.level) +  self.visit(node.title) + '</h{}>'.format(node.level)

    def visit_Wikilink(self, node, in_root=False):
        result = self._maybe_open_paragraph(in_root)

        # Get the rendered title.
        title = self.visit(node.title)
        url = get_article_url(self._base_url, title)

        # Display text can be optionally specified. Fall back to the article
        # title if it is not given.
        return result + '<a href="{}">'.format(url) + self.visit(node.text or node.title) + '</a>'

    def visit_ExternalLink(self, node, in_root=False):
        result = self._maybe_open_paragraph(in_root)

        # Display text can be optionally specified. Fall back to the URL if it
        # is not given.
        return result + '<a href="' + self.visit(node.url) + '">' + self.visit(node.title or node.url) + '</a>'

    def visit_Comment(self, node, in_root=False):
        # Write an HTML comment.
        return '<!-- {} -->'.format(node.contents)

    def visit_Text(self, node, in_root=False):
        # Write a text element.
        result = ''

        # Handle whether there's any lists to open.
        LIST_TAGS = {'ul', 'ol', 'dl'}
        TAGS_TO_CLOSE = LIST_TAGS.copy() | {'li', 'dt', 'p'}

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
                result += self._close_stack(stack_node)

            # Re-open anything that is pending..
            for list_tag, item_tag in self._pending_lists[i:]:
                self._stack.append(list_tag)
                result += '<{}>'.format(list_tag)

            # For the last pending list, also open the list item.
            item_tag = self._pending_lists[-1][1]
            result += '<{}>'.format(item_tag)
            self._stack.append(item_tag)

            # Reset the list.
            self._pending_lists = []

        elif in_root:
            # TODO

            # If this node isn't nested inside of anything else it might be
            # wrapped in a paragraph.
            if not self._stack and node.value.strip():
                result += '<p>'
                self._stack.append('p')

        result += html.escape(node.value, quote=False)

        # Certain tags get closed when there's a line break.
        num_new_lines = len(node.value) - len(node.value.rstrip('\n'))

        for i in range(num_new_lines):
            # Since _close_stack mutates the _stack, check on each iteration if
            # _stack is still truth-y.
            if not self._stack:
                break

            # Close an element in the stack.
            if self._stack[-1] in TAGS_TO_CLOSE:
                result += self._close_stack(self._stack[-1])

        return result

    def visit_Template(self, node, in_root=False):
        # Render the key into a string. This handles weird nested cases, e.g.
        # {{f{{text|oo}}bar}}.
        template_name = self.visit(node.name).strip()

        # Because each parameter's name and value might include other templates,
        # etc. these need to be rendered in the context of the template call.
        context = OrderedDict()
        for param in node.params:
            # See https://meta.wikimedia.org/wiki/Help:Template#Parameters
            # for information about stripping whitespace around parameters.
            param_name = self.visit(param.name).strip()
            param_value = self.visit(param.value)

            # Only named parameters strip whitespace around the value.
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
                return str(node)
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

                return function(function_context)

        # Otherwise, this is a normal template.
        else:
            try:
                template = self._template_store[template_name]
            except KeyError:
                # Template was not found, simply output the template call.
                return str(node)
            else:
                # Render the template in only the context of its parameters.
                composer = WikicodeToHtmlComposer(
                    self._base_url,
                    template_store=self._template_store,
                    context=context)
                return composer.visit(template, None)

    def visit_Argument(self, node, in_root=False):
        # There's no provided values, so just render the string.
        # Templates have special handling for Arguments.
        param_name = self.visit(node.name).strip()

        # Get the parameter's value from the context (the call to the
        # template we're rendering).
        try:
            return self._context[param_name]
        except KeyError:
            # No parameter with this name was given.

            # Use a default value if it exists, otherwise just render the
            # parameter as a string.
            if node.default is not None:
                # Render the default value.
                return self.visit(node.default)

            else:
                return str(node)

    def visit_HTMLEntity(self, node, in_root=False):
        # Write the original HTML entity.
        return self._maybe_open_paragraph(in_root) + str(node)

    def compose(self, node):
        """Converts Wikicode or Node objects to HTML."""
        result = self.visit(node, True)
        # Ensure the stack is closed at the end.
        for current_tag in reversed(self._stack):
            result += '</{}>'.format(current_tag)
        return result
