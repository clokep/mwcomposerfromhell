from mwparserfromhell.definitions import get_html_tag, MARKUP_TO_HTML
from mwparserfromhell.nodes import Comment, ExternalLink, Tag, Text, Wikilink

# The MARKUP_TO_HTML is missing a few things...this duck punches them in.
MARKUP_TO_HTML.update({
    "''": 'i',
})


def format_wikicode(wikicode):
    """Returns Unicode of Wikicode converted to HTML."""
    result = u''

    for node in wikicode.ifilter(recursive=False):
        if isinstance(node, Tag):
            # Get the HTML tag for this node.
            tag = get_html_tag(node.wiki_markup)

            # Convert all the children to HTML.
            inner = ''.join(map(format_wikicode, node.__children__()))

            # Create an HTML tag.
            # TODO Handle attributes.
            result += '<{}>{}</{}>'.format(tag, inner, tag)
        else:
            result += str(node)

    return result
