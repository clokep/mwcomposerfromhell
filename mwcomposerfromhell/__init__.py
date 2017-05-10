from mwparserfromhell.definitions import MARKUP_TO_HTML
from mwparserfromhell.nodes import ExternalLink, Tag, Template, Wikilink
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
        # Convert all the children to HTML.
        inner = u''.join(map(format_wikicode, obj.__children__()))

        # Self closing tags don't need an end tag, this produces "broken" HTML,
        # but readers should handle it fine.
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
        return u'<a href="{}">{}</a>'.format(wiki_url(obj.title), format_wikicode(text))

    elif isinstance(obj, ExternalLink):
        # Different text can be specified, or falls back to the URL.
        text = obj.title or obj.url
        return u'<a href="{}">{}</a>'.format(obj.url, format_wikicode(text))

    elif isinstance(obj, (list, tuple)):
        # If the object is iterable, just handle each item separately.
        result = u''
        for node in obj:
            result += format_wikicode(node)
        return result
    else:
        return str(obj)
