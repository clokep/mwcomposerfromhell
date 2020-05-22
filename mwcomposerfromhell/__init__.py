from mwcomposerfromhell.composer import HtmlComposingError, WikicodeToHtmlComposer  # noqa: F401
from mwcomposerfromhell.namespace import ArticleResolver, Namespace  # noqa: F401


def compose(wikicode: str) -> str:
    """One-shot to convert an object from parsed Wikicode to HTML."""
    composer = WikicodeToHtmlComposer()
    return composer.compose(wikicode)
