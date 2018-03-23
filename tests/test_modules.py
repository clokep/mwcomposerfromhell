import mwparserfromhell

from mwcomposerfromhell.composer import WikicodeToHtmlComposer


def test_len():
    """The length of a string."""
    wikicode = mwparserfromhell.parse('{{#invoke:String|len|target_string}}')
    result = WikicodeToHtmlComposer().compose(wikicode)
    assert result == '13'


def test_len_named():
    """The length of a string."""
    wikicode = mwparserfromhell.parse('{{#invoke:String|len|s=target_string}}')
    result = WikicodeToHtmlComposer().compose(wikicode)
    assert result == '13'
