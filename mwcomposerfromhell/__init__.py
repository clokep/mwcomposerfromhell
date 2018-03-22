from mwcomposerfromhell.composer import HtmlComposingError, WikicodeToHtmlComposer


def compose(obj):
    """One-shot compose an object from parsed Wikicode."""
    return WikicodeToHtmlComposer().compose(obj)
