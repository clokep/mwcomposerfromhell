from urllib.parse import quote as url_quote

from mwparserfromhell.definitions import MARKUP_TO_HTML
from mwparserfromhell.nodes import ExternalLink, Tag, Template, Wikilink
from mwparserfromhell.wikicode import Wikicode

# The MARKUP_TO_HTML is missing a few things...this duck punches them in.
MARKUP_TO_HTML.update({
    "''": 'i',
})


class WikicodeToHtmlComposer(object):
    """
    Format HTML from Parsed Wikicode.
    Note that this is not currently re-usable.
    https://en.wikipedia.org/wiki/Help:Wiki_markup
    """
    def __init__(self, base_url='https://en.wikipedia.org/wiki'):
        self._base_url = base_url

        self._article_url_format = base_url + '/{}'

    def _get_url(self, title):
        """Given a page title, return a URL suitable for linking."""
        safe_title = url_quote(title.encode('utf-8'))
        return self._article_url_format.format(safe_title)

    def _compose_parts(self, obj):
        """Takes an object and returns a generator that will compose one more pieces of HTML."""
        if isinstance(obj, Wikicode):
            for node in obj.ifilter(recursive=False):
                yield from self._compose_parts(node)

        elif isinstance(obj, Tag):
            # Create an HTML tag.
            # TODO Handle attributes.
            yield u'<{}>'.format(obj.tag)

            for child in obj.__children__():
                yield from self._compose_parts(child)

            # Self closing tags don't need an end tag, this produces "broken"
            # HTML, but readers should handle it fine.
            if not obj.self_closing:
                yield u'</{}>'.format(obj.closing_tag)

        elif isinstance(obj, Wikilink):
            # Different text can be specified, or falls back to the title.
            text = obj.text or obj.title
            url = self._get_url(obj.title)
            yield u'<a href="{}">{}</a>'.format(url, self.compose(text))

        elif isinstance(obj, ExternalLink):
            # Different text can be specified, or falls back to the URL.
            text = obj.title or obj.url
            yield u'<a href="{}">{}</a>'.format(obj.url, self.compose(text))

        elif isinstance(obj, (list, tuple)):
            # If the object is iterable, just handle each item separately.
            for node in obj:
                yield from self._compose_parts(self.compose(node))

        else:
             # TODO Raise?
            yield str(obj)

    def compose(self, obj):
        """Converts Wikicode or Node objects to HTML."""
        return ''.join(self._compose_parts(obj))
