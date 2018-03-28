from mwcomposerfromhell.composer import HtmlComposingError, WikicodeToHtmlComposer  # noqa: F401


def compose(obj):
    """One-shot compose an object from parsed Wikicode."""
    return WikicodeToHtmlComposer().compose(obj)
