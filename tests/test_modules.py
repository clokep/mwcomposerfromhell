import mwparserfromhell

from mwcomposerfromhell import compose


def test_len():
    """The length of a string."""
    wikicode = mwparserfromhell.parse('{{#invoke:String|len|target_string}}')
    assert compose(wikicode) == '13'


def test_len_named():
    """The length of a string."""
    wikicode = mwparserfromhell.parse('{{#invoke:String|len|s=target_string}}')
    assert compose(wikicode) == '13'


def test_capitalization():
    """MediaWiki treats the first character as case-insensitive."""
    wikicode = mwparserfromhell.parse('{{#invoke:string|len|s=target_string}}')
    assert compose(wikicode) == '13'


def test_unknown_module():
    """An unknown module gets rendered as is."""
    wikicode = mwparserfromhell.parse('{{#invoke:foo|bar}}')
    assert compose(wikicode) == '{{#invoke:foo|bar}}'


def test_unknown_function():
    """An unknown module gets rendered as is."""
    wikicode = mwparserfromhell.parse('{{#invoke:String|foobar}}')
    assert compose(wikicode) == '{{#invoke:String|foobar}}'
