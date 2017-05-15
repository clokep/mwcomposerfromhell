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
    """
    def __init__(self, base_url='https://en.wikipedia.org/wiki'):
        self._base_url = base_url

        self._article_url_format = base_url + '/{}'

    def _get_url(self, title):
        """Given a page title, return a URL suitable for linking."""
        safe_title = url_quote(title.encode('utf-8'))
        return self._article_url_format.format(safe_title)

    def compose(self, obj):
        """Converts Wikicode or Node objects to HTML."""
        if isinstance(obj, Wikicode):
            result = u''
            for node in obj.ifilter(recursive=False):
                result += self.compose(node)
            return result

        elif isinstance(obj, Tag):
            # Convert all the children to HTML.
            inner = u''.join(map(self.compose, obj.__children__()))

            # Self closing tags don't need an end tag, this produces "broken"
            # HTML, but readers should handle it fine.
            if not obj.self_closing:
                template = u'<{tag}>{inner}</{closing_tag}>'
            else:
                template = u'<{tag}>{inner}'

            # Create an HTML tag.
            # TODO Handle attributes.
            return template.format(tag=obj.tag, inner=inner, closing_tag=obj.closing_tag)

        elif isinstance(obj, Wikilink):
            # Different text can be specified, or falls back to the title.
            text = obj.text or obj.title
            url = self._get_url(obj.title)
            return u'<a href="{}">{}</a>'.format(url, self.compose(text))

        elif isinstance(obj, ExternalLink):
            # Different text can be specified, or falls back to the URL.
            text = obj.title or obj.url
            return u'<a href="{}">{}</a>'.format(obj.url, self.compose(text))

        elif isinstance(obj, (list, tuple)):
            # If the object is iterable, just handle each item separately.
            result = u''
            for node in obj:
                result += self.compose(node)
            return result

        else:
             # TODO Raise?
            return str(obj)
