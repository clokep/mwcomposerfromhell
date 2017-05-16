from urllib.parse import quote as url_quote

from mwparserfromhell.definitions import MARKUP_TO_HTML
from mwparserfromhell.nodes import Comment, ExternalLink, HTMLEntity, Tag, Template, Text, Wikilink
from mwparserfromhell.wikicode import Wikicode

# The MARKUP_TO_HTML is missing a few things...this duck punches them in.
MARKUP_TO_HTML.update({
    "''": 'i',
})


class UnknownNode(Exception):
    pass


class WikicodeToHtmlComposer(object):
    """
    Format HTML from Parsed Wikicode.
    Note that this is not currently re-usable.
    https://en.wikipedia.org/wiki/Help:Wiki_markup
    """
    def __init__(self, base_url='https://en.wikipedia.org/wiki'):
        self._base_url = base_url

        self._article_url_format = base_url + '/{}'

        # Track the currently open tags.
        self._stack = []

    def _get_url(self, title):
        """Given a page title, return a URL suitable for linking."""
        safe_title = url_quote(title.encode('utf-8'))
        return self._article_url_format.format(safe_title)

    def _close_stack(self, tag=None):
        """Close tags that are on the stack. It closes all tags until ``tag`` is found.
        If no tag to close is given the entire stack is closed.
        """
        # Close the entire stack.
        if tag is None:
            print("Closing the full stack.")
            for current_tag in reversed(self._stack):
                yield u'</{}>'.format(current_tag)
            return

        # If a tag was given, close all tags behind it (in reverse order).
        if tag not in self._stack:
            # TODO
            raise RuntimeError('Uh oh')

        while len(self._stack):
            current_tag = self._stack.pop()
            print("Removing {} from the stack.".format(current_tag))
            yield u'</{}>'.format(current_tag)

            if current_tag == tag:
                break

    def _require_parent(self, parent_tag, current_tag):
        """Ensure a particular tag is open on the stack, opens it if not."""
        try:
            child_after_parent = self._stack.index(current_tag) > self._stack.index(parent_tag)
        except ValueError:
            child_after_parent = False

        if parent_tag not in self._stack or child_after_parent:
            self._stack.append(parent_tag)
            yield u'<{}>'.format(parent_tag)

    def _compose_parts(self, obj):
        """Takes an object and returns a generator that will compose one more pieces of HTML."""
        if isinstance(obj, Wikicode):
            for node in obj.ifilter(recursive=False):
                yield from self._compose_parts(node)

        elif isinstance(obj, Tag):
            # Some tags require a parent tag to be open first, but get grouped
            # if one is already open.
            if obj.wiki_markup == '*':
                yield from self._require_parent('ul', 'li')
            elif obj.wiki_markup == '#':
                yield from self._require_parent('ol', 'li')
            elif obj.wiki_markup == ';':
                yield from self._require_parent('dl', 'dt')

            # Create an HTML tag.
            # TODO Handle attributes.
            yield u'<{}>'.format(obj.tag)

            # We just opened a tag, woot!
            self._stack.append(obj.tag)
            print("Adding {} to the stack.".format(obj.tag))

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
            yield u'<a href="{}">{}</a>'.format(url, self._compose_parts(text))

        elif isinstance(obj, ExternalLink):
            # Different text can be specified, or falls back to the URL.
            text = obj.title or obj.url
            yield u'<a href="{}">{}</a>'.format(obj.url, self._compose_parts(text))

        elif isinstance(obj, Comment):
            yield u'<!-- {} -->'.format(obj.contents)

        elif isinstance(obj, Text):
            yield obj.value

        elif isinstance(obj, (HTMLEntity, Template)):
            # TODO
            yield str(obj)

        elif isinstance(obj, (list, tuple)):
            # If the object is iterable, just handle each item separately.
            for node in obj:
                yield from self._compose_parts(node)

        else:
            raise UnknownNode(u'Unknown node type: {}'.format(type(obj)))

    def compose(self, obj):
        """Converts Wikicode or Node objects to HTML."""
        # TODO Add a guard that this can only be called once at a time.

        result = u''

        # Generate each part and append it to the result.
        for part in self._compose_parts(obj):
            result += part

            # Certain tags get closed when there's a line break.
            if self._stack:
                for c in reversed(part):
                    if c == '\n':
                        elements_to_close = ['li', 'ul', 'ol', 'dl', 'dt']
                        # Close an element in the stack.
                        if self._stack[-1] in elements_to_close:
                            for part in self._close_stack(self._stack[-1]):
                                result += part
                    else:
                        break

        # If any parts of the stack are still open, close them.
        for part in self._close_stack():
            result += part

        return result
