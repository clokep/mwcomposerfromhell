from mwcomposerfromhell.composer import HtmlComposingError, WikicodeToHtmlComposer  # noqa: F401


def compose(wikicode: str) -> str:
    """One-shot to convert an object from parsed Wikicode to HTML."""
    composer = WikicodeToHtmlComposer()
    return composer.compose(wikicode)
