from mwparserfromhell.definitions import get_html_tag, MARKUP_TO_HTML
from mwparserfromhell.nodes import Comment, ExternalLink, Tag, Text, Wikilink
from mwparserfromhell.wikicode import Wikicode

# The MARKUP_TO_HTML is missing a few things...this duck punches them in.
MARKUP_TO_HTML.update({
    "''": 'i',
})


def format_wikicode(obj):
    """Returns Unicode of a Wikicode or Node object converted to HTML."""
    if isinstance(obj, Wikicode):
        result = u''
        for node in obj.ifilter(recursive=False):
            result += format_wikicode(node)
        return result

    if isinstance(obj, Tag):
        # Get the HTML tag for this node.
        tag = get_html_tag(obj.wiki_markup)

        # Convert all the children to HTML.
        inner = ''.join(map(format_wikicode, obj.__children__()))

        # Create an HTML tag.
        # TODO Handle attributes.
        return '<{}>{}</{}>'.format(tag, inner, tag)

    elif isinstance(obj, Wikilink):
        # Different text can be specified, or falls back to the title.
        text = obj.text or obj.title
        return u'<a href="{}">{}</a>'.format(wiki_url(obj.title), format_wikicode(text))

    elif isinstance(obj, ExternalLink):
        # Different text can be specified, or falls back to the URL.
        text = obj.title or obj.url
        return u'<a href="{}">{}</a>'.format(obj.url, format_wikicode(text))

    else:
        return str(obj)
