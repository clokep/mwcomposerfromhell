import mwparserfromhell

from mwcomposerfromhell import compose


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


def test_abutting_lists():
    """Lists next to each other should not be combined."""
    content = """* List 1
* List 1

* List 2
* List 2
"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<ul><li> List 1\n</li><li> List 1\n\n</li></ul><ul><li> List 2\n</li><li> List 2\n</li></ul>'


def test_definition_list():
    """A definition list with no items."""
    content = ";Foobar"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<dl><dt>Foobar</dt></dl>'


def test_definition_list_single_item():
    """A definition list with no items."""
    content = ";Foo : Bar"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<dl><dt>Foo </dt><dd> Bar</dd></dl>'


def test_definition_list_multiple_items():
    """A definition list with no items."""
    content = """;Foo
: Bar
: Baz
"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<dl><dt>Foo\n</dt><dd> Bar\n</dd><dd> Baz\n</dd></dl>'


def test_nested_list():
    """A nested list with additional line breaks afterward properly closes the stack."""
    content = """*Foo
**Bar

<!--Comment-->

"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<ul><li>Foo\n</li><ul><li>Bar\n\n</li></ul><!-- Comment -->\n\n</ul>'


def test_nested_list_types():
    """Certain list types cannot be contained inside each other."""
    content = """;Foo
*Bar
"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<dl><dt>Foo\n</dt></dl><ul><li>Bar\n</li></ul>'


def test_nested_list_types2():
    """Certain list types cannot be contained inside each other."""
    content = """*Foo
;Bar
"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<ul><li>Foo\n</li></ul><dl><dt>Bar\n</dt></dl>'


def test_list_with_formatting():
    """A list that has formatted entries."""
    content = """* '''foo'''
* ''bar''
"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '''<ul><li> <b>foo</b>
</li><li> <i>bar</i>
</li></ul>'''
