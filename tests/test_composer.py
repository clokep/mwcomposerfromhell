import mwparserfromhell

from mwcomposerfromhell.composer import WikicodeToHtmlComposer


def test_formatting():
    """Test that simple formatting works."""
    content = "''foobar''"
    wikicode = mwparserfromhell.parse(content)
    composer = WikicodeToHtmlComposer()
    assert composer.compose(wikicode) == '<i>foobar</i>'


def test_formatting_link():
    """Ensure an external link is rendered properly with a title that's formatted."""
    content = "[http://google.com ''foobar'']"
    wikicode = mwparserfromhell.parse(content)
    composer = WikicodeToHtmlComposer()
    assert composer.compose(wikicode) == '<a href="http://google.com"><i>foobar</i></a>'


def test_internal_link():
    """Ensure an internal link is rendered properly."""
    content = "[[Foobar]]"
    wikicode = mwparserfromhell.parse(content)
    composer = WikicodeToHtmlComposer()
    assert composer.compose(wikicode) == '<a href="https://en.wikipedia.org/wiki/Foobar">Foobar</a>'


def test_internal_link_title():
    """Ensure an internal link with a title is rendered properly."""
    content = "[[Foobar|fuzzbar]]"
    wikicode = mwparserfromhell.parse(content)
    composer = WikicodeToHtmlComposer()
    assert composer.compose(wikicode) == '<a href="https://en.wikipedia.org/wiki/Foobar">fuzzbar</a>'


def test_list():
    """Ensure a list is rendered properly."""
    content = "* Foobar"
    wikicode = mwparserfromhell.parse(content)
    composer = WikicodeToHtmlComposer()
    assert composer.compose(wikicode) == '<ul><li> Foobar</li></ul>'


def test_subitem_list():
    """Ensure a list with another list inside of it is rendered properly."""
    content = "* Foobar\n** Subitem"
    wikicode = mwparserfromhell.parse(content)
    composer = WikicodeToHtmlComposer()
    assert composer.compose(wikicode) == '<ul><li> Foobar\n</li><ul><li> Subitem</li></ul></ul>'


def test_subitem_list_complex():
    """Ensure a list with another list inside of it is rendered properly."""
    content = "* Foobar\n** Subitem\n* Barfoo"
    wikicode = mwparserfromhell.parse(content)
    composer = WikicodeToHtmlComposer()
    assert composer.compose(wikicode) == '<ul><li> Foobar\n</li><ul><li> Subitem\n</li></ul><li> Barfoo</li></ul>'


def test_definition_list():
    """A definition list with no items."""
    content = ";Foobar"
    wikicode = mwparserfromhell.parse(content)
    composer = WikicodeToHtmlComposer()
    result = composer.compose(wikicode)
    assert result == '<dl><dt>Foobar</dt></dl>'


def test_nested_list():
    """A nested list with additional line breaks afterward properly closes the stack."""
    content = """*Foo
**Bar

<!--Comment-->

"""
    wikicode = mwparserfromhell.parse(content)
    composer = WikicodeToHtmlComposer()
    result = composer.compose(wikicode)
    assert result == '<ul><li>Foo\n</li><ul><li>Bar\n\n</li></ul><!-- Comment -->\n\n</ul>'
