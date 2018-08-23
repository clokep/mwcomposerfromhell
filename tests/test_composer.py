import mwparserfromhell

from mwcomposerfromhell import compose


def test_formatting():
    """Test that simple formatting works."""
    content = "''foobar''"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<i>foobar</i>'


def test_formatting_link():
    """Ensure an external link is rendered properly with a title that's formatted."""
    content = "[http://google.com ''foobar'']"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<a href="http://google.com"><i>foobar</i></a>'


def test_internal_link():
    """Ensure an internal link is rendered properly."""
    content = "[[Foobar]]"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<a href="https://en.wikipedia.org/wiki/Foobar">Foobar</a>'


def test_internal_link_title():
    """Ensure an internal link with a title is rendered properly."""
    content = "[[Foobar|fuzzbar]]"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<a href="https://en.wikipedia.org/wiki/Foobar">fuzzbar</a>'


def test_list():
    """Ensure a list is rendered properly."""
    content = "* Foobar"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<ul><li> Foobar</li></ul>'


def test_subitem_list():
    """Ensure a list with another list inside of it is rendered properly."""
    content = "* Foobar\n** Subitem"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<ul><li> Foobar\n</li><ul><li> Subitem</li></ul></ul>'


def test_subitem_list_complex():
    """Ensure a list with another list inside of it is rendered properly."""
    content = "* Foobar\n** Subitem\n* Barfoo"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<ul><li> Foobar\n</li><ul><li> Subitem\n</li></ul><li> Barfoo</li></ul>'


def test_definition_list():
    """A definition list with no items."""
    content = ";Foobar"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<dl><dt>Foobar</dt></dl>'


def test_nested_list():
    """A nested list with additional line breaks afterward properly closes the stack."""
    content = """*Foo
**Bar

<!--Comment-->

"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<ul><li>Foo\n</li><ul><li>Bar\n\n</li></ul><!-- Comment -->\n\n</ul>'


def test_list_with_formatting():
    """A list that has formatted entries."""
    content = """* '''foo'''
* ''bar''
"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '''<ul><li> <b>foo</b>
</li><li> <i>bar</i>
</li></ul>'''


def test_heading():
    """Test a heading."""
    content = "=== Foobar ==="
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<h3> Foobar </h3>'


def test_entity():
    """Test HTML entities."""
    content = "&Sigma; &#931; &#x3a3;"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '&Sigma; &#931; &#x3a3;'


def test_table():
    """Test an wiki table."""
    content = """{|
|-
! Header 1 !! Header 2 !! Header 3
|-
| Example 1a || Example 2a || Example 3a
|-
| Example 1b || Example 2b || Example 3b
|}"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == """<table><tr><th> Header 1 </th><th> Header 2 </th><th> Header 3
</th></tr><tr><td> Example 1a </td><td> Example 2a </td><td> Example 3a
</td></tr><tr><td> Example 1b </td><td> Example 2b </td><td> Example 3b
</td></tr></table>"""


def test_table_class():
    """Test an wiki table."""
    content = """{| class="wikitable"
|-
! Header 1 !! Header 2
|-
| Example 1 || Example 2
|}"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == """<table class="wikitable"><tr><th> Header 1 </th><th> Header 2
</th></tr><tr><td> Example 1 </td><td> Example 2
</td></tr></table>"""
