from mwcomposerfromhell.composer import HtmlComposingError, WikicodeToHtmlComposer  # noqa: F401


def compose(wikicode):
    """One-shot to convert an object from parsed Wikicode to HTML."""
    composer = WikicodeToHtmlComposer()
    composer.compose(wikicode)
    return composer.stream.getvalue()
