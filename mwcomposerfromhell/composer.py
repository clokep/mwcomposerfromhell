from collections import OrderedDict
import html
import re
from typing import Dict, List, Optional, Set, Tuple, Union
from urllib.parse import quote as urlquote, urlencode

from mwparserfromhell import nodes

from mwcomposerfromhell.magic_words import MAGIC_WORDS
from mwcomposerfromhell.modules import ModuleStore, UnknownModule
from mwcomposerfromhell.namespace import ArticleNotFound, ArticleResolver
from mwcomposerfromhell.nodes import Wikilink

# The markup for different lists mapped to the list tag and list item tag.
MARKUP_TO_LIST = {
    # Unordered list.
    '*': ('ul', 'li'),
    # Ordered list.
    '#': ('ol', 'li'),
    # Definition lists.
    ';': ('dl', 'dt'),
    ':': ('dl', 'dd'),
}

# The markup for tags which are inline, as opposed to block.
INLINE_TAGS = {"''", "'''"}

# Tags that represent a list or list items.
LIST_TAGS = {'ul', 'ol', 'li', 'dl', 'dt', 'dd'}

# One or more new-line.
LINE_BREAK_PATTERN = re.compile(r'(\n+)')
# Patterns used to strip comments.
LINE_BREAK_SPACES_PATTERN = re.compile(r'\n *')
SPACES_LINE_BREAK_PATTERN = re.compile(r' *\n')
# Link trails are any words followed by a space or new-line.
LINK_TRAIL_PATTERN = re.compile(r'^([a-zA-Z]+)\b')

# The type for a Template Context.
TemplateContext = Dict[str, str]


class UnknownNode(Exception):
    pass


class TemplateLoop(Exception):
    """A template loop was found, bail rendering."""


class HtmlComposingError(Exception):
    pass


def _safe_title(title: str) -> str:
    """MediaWiki replaces spaces with underscores, then URL encodes."""
    return title.replace(' ', '_')


def get_article_url(base_url: str, title: str) -> str:
    """Given a page title, return a URL suitable for linking."""
    return '{}/{}'.format(base_url, urlquote(_safe_title(title), safe='/:'))


def get_edit_url(base_url: str, title: str) -> str:
    """Given a page title, return a URL suitable for editing that page."""
    params = (
        ('title', _safe_title(title)),
        ('action', 'edit'),
        ('redlink', '1'),
    )
    return '{}?{}'.format(base_url, html.escape(urlencode(params, safe=':')))


class WikiNodeVisitor:
    def visit(self, node, in_root: bool = False) -> str:
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
                 base_url: str = '/wiki',
                 resolver: Optional[ArticleResolver] = None,
                 red_links: bool = False,
                 context: Optional[TemplateContext] = None,
                 open_templates: Optional[Set[str]] = None):

        # The base URL should be the root that articles sit in.
        self._base_url = base_url.rstrip('/')
        # Whether to render links to unknown articles as red links or normal links.
        self._red_links = red_links

        self._pending_lists = []  # type: List[str]

        # Track the currently open tags.
        self._stack = []  # type: List[str]

        # Track current templates to avoid a loop.
        self._open_templates = open_templates or set()

        self._context = context or {}

        # A place to lookup templates.
        if resolver is None:
            resolver = ArticleResolver()
        elif not isinstance(resolver, ArticleResolver):
            raise ValueError('resolver must be an instance of ArticleResolver')
        self._resolver = resolver

        # A place to lookup modules.
        self._module_store = ModuleStore()

    def _maybe_open_tag(self, in_root: bool) -> str:
        """
        Handle the logic for whether this node gets wrapped in a list or a paragraph.
        """
        # If the node is not currently in the "root" Wikicode, nothing is done.
        if not in_root:
            return ''

        # Handle whether there's any lists to open.
        if self._pending_lists:
            # The overall algorithm for deciding which tags to open and which to
            # close is nuanced:
            #
            # 1. Calculate the portion of lists and list items that are identical.
            # 2. Close the end of what doesn't match.
            # 3. Open the new tags.
            result = ''

            # The currently open lists.
            stack_lists = [list_tag for list_tag in self._stack if list_tag in LIST_TAGS]

            # Don't consider the latest list item to open in the comparison, it
            # always needs to be opened.
            shortest = min([len(stack_lists), len(self._pending_lists) - 1])
            # Find the index of the last matching item.
            for i in range(shortest):
                if stack_lists[i] != self._pending_lists[i]:
                    break
            else:
                i = shortest

            # Close anything past the matching items.
            for stack_node in reversed(stack_lists[i:]):
                result += self._close_stack(stack_node)

            # Open any items that are left from the pending list.
            for tag in self._pending_lists[i:]:
                self._stack.append(tag)
                result += '<{}>'.format(tag)

            # Reset the pending list.
            self._pending_lists = []
            return result

        # Paragraphs do not go inside of other elements.
        if not self._stack:
            self._stack.append('p')
            return '<p>'

        # Otherwise, do nothing.
        return ''

    def _close_stack(self, tag: str) -> str:
        """Close tags that are on the stack. It closes all tags until ``tag`` is found."""
        # For the given tag, close all tags behind it (in reverse order).
        result = ''
        while len(self._stack):
            current_tag = self._stack.pop()
            result += '</{}>'.format(current_tag)

            if current_tag == tag:
                break

        return result

    def _fix_nodes(self, nodes_iterator):
        """
        Iterate through nodes making some fixes:

        * Skip comment nodes.
        * Combine adjecent text nodes.
        * Handle link trails.

        Transforms [Text, Comment, Text] -> [Text]
        """
        prev_node = None
        for node in nodes_iterator:
            # Skip comment nodes.
            if isinstance(node, nodes.Comment):
                continue

            # Convert Wikilinks to the mwcomposerfromhell subclass.
            if isinstance(node, nodes.Wikilink):
                node = Wikilink(node.title, node.text)

            # Two (now adjacent) text nodes are combined.
            if isinstance(prev_node, nodes.Text) and isinstance(node, nodes.Text):
                # A removed comment strips any spaces on the line it was on,
                # plus a single newline. In order to get all whitespace, look at
                # both text nodes.
                prev = LINE_BREAK_SPACES_PATTERN.sub('', prev_node.value, count=1)
                current = SPACES_LINE_BREAK_PATTERN.sub('\n', node.value, count=1)

                prev_node = nodes.Text(value=prev + current)
                continue

            elif isinstance(prev_node, Wikilink) and isinstance(node, nodes.Text):
                # Try to find a link trail and apply it to the previous link.
                # TODO This should NOT apply if the previous link was to an image.
                match = LINK_TRAIL_PATTERN.match(node.value)
                if match:
                    # The link gets the link trail added to the text.
                    prev_node = Wikilink(prev_node.title, prev_node.text, match[1])
                    # The text gets the link trailed removed from it.
                    node = nodes.Text(value=node.value[len(match[1]):])

            # Otherwise, yield the previous node and store the current one.
            if prev_node:
                yield prev_node
            prev_node = node

        # Yield the last node.
        if prev_node:
            yield prev_node

    def _get_edit_link(self, title: str, text: str) -> str:
        # TODO This should be configurable.
        url = get_edit_url('/index.php', title)
        title += ' (page does not exist)'
        return '<a href="{}" class="new" title="{}">'.format(url, title) + text + '</a>'

    def visit_Wikicode(self, node, in_root: bool = False) -> str:
        return ''.join(map(lambda n: self.visit(n, in_root), self._fix_nodes(node.nodes)))

    def visit_Tag(self, node, in_root: bool = False) -> str:
        result = ''

        # List tags require a parent tag to be opened first, but get grouped
        # together if one is already open.
        if node.wiki_markup in MARKUP_TO_LIST:
            list_tag, item_tag = MARKUP_TO_LIST[node.wiki_markup]
            # Mark that this tag needs to be opened.
            self._pending_lists.extend((list_tag, item_tag))

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

            # nowiki tags do not end up in the resulting content. Note that the
            # parser handles the nowiki tag: the contents should just be a Text
            # node.
            if tag == 'nowiki':
                if node.contents:
                    return self.visit(node.contents)
                return ''

            # noinclude and includeonly tags do not end up in the resulting
            # content. Their contents depend on whether the current content is
            # transcluded or not.
            #
            # See https://www.mediawiki.org/wiki/Transclusion
            if tag == 'noinclude':
                if not self._open_templates and node.contents:
                    return self.visit(node.contents)
                return ''
            if tag == 'includeonly':
                if self._open_templates and node.contents:
                    return self.visit(node.contents)
                return ''

            # Maybe wrap the tag in a paragraph, notably this gets ignored for
            # tables and some other tags.
            if node.wiki_markup in INLINE_TAGS:
                result += self._maybe_open_tag(in_root)

            # Create an HTML tag.
            result += '<' + tag
            for attr in node.attributes:
                result += self.visit(attr)
            if node.self_closing:
                result += ' /'
            result += '>'

            # If this is not a self-closing tag, add it to the stack.
            if not node.self_closing:
                self._stack.append(tag)

        # Handle anything inside of the tag.
        if node.contents:
            result += self.visit(node.contents)

        # If this is not self-closing, close this tag and any other open tags
        # after it.
        # TODO This only happens to work because lists are not self-closing.
        if not node.self_closing:
            result += self._close_stack(tag)

        return result

    def visit_Attribute(self, node, in_root: bool = False) -> str:
        # Just use the string version of the attribute, it does all the parsing
        # that we want.
        return str(node)

    def visit_Heading(self, node, in_root: bool = False) -> str:
        return '<h{}>'.format(node.level) + self.visit(node.title) + '</h{}>'.format(node.level)

    def visit_Wikilink(self, node, in_root: bool = False) -> str:
        result = self._maybe_open_tag(in_root)

        # Get the rendered title.
        title = self.visit(node.title).title()
        url = get_article_url(self._base_url, title)
        text = self.visit(node.text or node.title) + (node.trail or '')

        # Figure out whether the article exists or not.
        article_exists = True
        if self._red_links:
            try:
                self._resolver.get_article(title, default_namespace='')
            except ArticleNotFound:
                article_exists = False

        # Display text can be optionally specified. Fall back to the article
        # title if it is not given.
        if article_exists:
            return result + '<a href="{}" title="{}">'.format(url, title) + text + '</a>'
        else:
            return result + self._get_edit_link(title, text)

    def visit_ExternalLink(self, node, in_root: bool = False) -> str:
        """
        Generate the HTML for an external link.

        External links come in a few forms:

        * A raw link: https://en.wikipedia.org/
        * A bracketed link: [https://en.wikipedia.org/]
        * A link with a title: [https://en.wikipedia.org/ Wikipedia]
        """
        result = self._maybe_open_tag(in_root)

        # Display text can be optionally specified. Fall back to the URL if it
        # is not given.
        text = self.visit(node.title or node.url)

        extra = ''
        if not node.brackets:
            extra = 'rel="nofollow" class="external free" '

        return result + '<a ' + extra + 'href="' + self.visit(node.url) + '">' + text + '</a>'

    def visit_Comment(self, node, in_root: bool = False) -> str:
        """HTML comments just get ignored."""
        return ''

    def visit_Text(self, node, in_root: bool = False) -> str:
        # Write a text element.
        result = ''

        # Render the text.
        text_result = html.escape(node.value, quote=False)

        # Handle newlines, which modify paragraphs and how elements get closed.
        # Filter out blank strings after splitting on newlines.
        chunks = list(filter(None, LINE_BREAK_PATTERN.split(text_result)))

        for it, chunk in enumerate(chunks):
            # Each chunk will either be all newlines, or just content.
            if '\n' in chunk:
                line_breaks = len(chunk)

                if it > 0 or line_breaks == 1 or line_breaks == 2:
                    result += '\n'

                # If more than two newlines exist, close previous paragraphs.
                if line_breaks >= 2:
                    result += self._close_stack('p')

                # If this node isn't nested inside of anything else it might be
                # wrapped in a paragraph.
                if not self._stack and in_root:
                    # A paragraph with a line break is added for every two
                    # additional newlines.
                    additional_p = max((line_breaks - 2) // 2, 0)
                    result += additional_p * '<p><br />\n</p>'

                    # If there is more content after this set of newlines, or
                    # this is the last chunk of content and there are 3 line
                    # breaks.
                    last_chunk = it == len(chunks) - 1
                    if not last_chunk or (last_chunk and line_breaks == 3):
                        result += '<p>'
                        self._stack.append('p')

                        # An odd number of newlines get a line break inside of
                        # the paragraph.
                        if line_breaks > 1 and line_breaks % 2 == 1:
                            result += '<br />\n'
            else:
                result += self._maybe_open_tag(in_root)
                result += chunk

        return result

    def visit_Template(self, node, in_root: bool = False) -> str:
        # Render the key into a string. This handles weird nested cases, e.g.
        # {{f{{text|oo}}bar}}.
        template_name = self.visit(node.name).strip()

        # Because each parameter's name and value might include other templates,
        # etc. these need to be rendered in the context of the template call.
        context = OrderedDict()  # type: OrderedDict[str, str]
        for param in node.params:
            # See https://meta.wikimedia.org/wiki/Help:Template#Parameters
            # for information about stripping whitespace around parameters.
            param_name = self.visit(param.name).strip()
            param_value = self.visit(param.value)

            # Only named parameters strip whitespace around the value.
            if param.showkey:
                param_value = param_value.strip()

            context[param_name] = param_value

        # Handle magic words: https://www.mediawiki.org/wiki/Help:Magic_words
        #
        # The template name might have a colon in it, if so there's a
        # "magic word" or a namespace, followed by a single parameter.
        magic_word, _, param = template_name.partition(':')

        if magic_word in MAGIC_WORDS:
            return self._maybe_open_tag(in_root) + MAGIC_WORDS[magic_word]()

        # This represents a script, see https://www.mediawiki.org/wiki/Extension:Scribunto
        elif magic_word == '#invoke':

            try:
                # Get the function names from the parameters.
                _, function_name = context.popitem(last=False)

                # Get the actual function.
                function = self._module_store.get_function(param, function_name)
            except UnknownModule:
                # TODO
                return str(node)
            else:
                # Call the script with the provided context. Note that we
                # can't do anything fancy with the parameters because
                # MediaWiki lets you have non-named parameters after named
                # parameters. We do need to re-number them, however, so that
                # they begin at '1' and not '2'.
                function_context = OrderedDict()  # OrderedDict[str, str]
                for key, value in context.items():  # type: Tuple[Union[str, int], str]
                    try:
                        key = int(key) - 1
                    except ValueError:
                        pass
                    function_context[str(key)] = value

                return function(function_context)

        # Otherwise, this is a normal template.
        else:
            # Ensure that we don't end up in an infinite loop of templates.
            if template_name in self._open_templates:
                raise TemplateLoop(template_name)
            self._open_templates.add(template_name)

            try:
                template = self._resolver.get_article(template_name, 'Template')
            except ArticleNotFound:
                # Template was not found.
                result = self._maybe_open_tag(in_root)

                # When transcluding a non-template
                if self._red_links:
                    # Render an edit link.
                    return result + self._get_edit_link(template_name, template_name)
                else:
                    # Otherwise, simply output the template call.
                    return result + self._maybe_open_tag(in_root) + str(node)
            else:
                # Render the template in only the context of its parameters.
                composer = WikicodeToHtmlComposer(
                    self._base_url,
                    resolver=self._resolver,
                    context=context,
                    open_templates=self._open_templates)
                result = composer.visit(template, in_root)
                # Ensure the stack is closed at the end.
                for current_tag in reversed(composer._stack):
                    result += '</{}>'.format(current_tag)

                # Remove it from the open templates.
                self._open_templates.remove(template_name)

                return result

    def visit_Argument(self, node, in_root: bool = False) -> str:
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

    def visit_HTMLEntity(self, node, in_root: bool = False) -> str:
        # Write the original HTML entity.
        return self._maybe_open_tag(in_root) + str(node)

    def compose(self, node) -> str:
        """Converts Wikicode or Node objects to HTML."""
        try:
            result = self.visit(node, True)
            # Ensure the stack is closed at the end.
            for current_tag in reversed(self._stack):
                result += '</{}>'.format(current_tag)
            return result
        except TemplateLoop as e:
            # The template name is the first argument.
            template_name = e.args[0]
            # Capitalize the first letter of the template name.
            template_name = 'Template:' + template_name[0].upper() + template_name[1:]
            # TODO Should this create an ExternalLink and use that?
            url = get_article_url(self._base_url, template_name)
            return ('<p><span class="error">Template loop detected: ' +
                    '<a href="{url}" title="{template_name}">{template_name}</a>' +
                    '</span>\n</p>').format(url=url, template_name=template_name)
