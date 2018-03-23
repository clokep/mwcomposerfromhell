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


def test_capitalization():
    """MediaWiki treats the first character as case-insensitive."""
    wikicode = mwparserfromhell.parse('{{#invoke:string|len|s=target_string}}')
    result = WikicodeToHtmlComposer().compose(wikicode)
    assert result == '13'


def test_unknown_module():
    """An unknown module gets rendered as is."""
    wikicode = mwparserfromhell.parse('{{#invoke:foo|bar}}')
    result = WikicodeToHtmlComposer().compose(wikicode)
    assert result == '{{#invoke:foo|bar}}'


def test_unknown_function():
    """An unknown module gets rendered as is."""
    wikicode = mwparserfromhell.parse('{{#invoke:String|foobar}}')
    result = WikicodeToHtmlComposer().compose(wikicode)
    assert result == '{{#invoke:String|foobar}}'
