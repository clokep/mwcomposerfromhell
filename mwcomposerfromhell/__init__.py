from mwcomposerfromhell.composer import (  # noqa: F401
    HtmlComposingError,
    WikicodeToHtmlComposer,
)
from mwcomposerfromhell.namespace import ArticleResolver, Namespace  # noqa: F401


def compose(wikicode: str) -> str:
    """One-shot to convert an object from parsed Wikicode to HTML."""
    composer = WikicodeToHtmlComposer()
    return composer.compose(wikicode)
