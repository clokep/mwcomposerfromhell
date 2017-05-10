import mwparserfromhell

from mwcomposerfromhell import format_wikicode

def test_formatting():
    content = "''foobar''"
    wikicode = mwparserfromhell.parse(content)
    assert format_wikicode(wikicode) == '<i>foobar</i>'
