import mwparserfromhell

from mwcomposerfromhell import format_wikicode

def test_formatting():
    content = "''foobar''"
    wikicode = mwparserfromhell.parse(content)
    assert format_wikicode(wikicode) == '<i>foobar</i>'


def test_formatting_link():
    content = "[http://google.com ''foobar'']"
    wikicode = mwparserfromhell.parse(content)
    assert format_wikicode(wikicode) == '<a href="http://google.com"><i>foobar</i></a>'
