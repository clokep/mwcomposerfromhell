import mwparserfromhell
import pytest

from mwcomposerfromhell import compose, WikicodeToHtmlComposer
from mwcomposerfromhell.composer import UnknownNode


def test_formatting():
    """Test that simple formatting works."""
    content = "''foobar''"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<p><i>foobar</i></p>'


def test_formatting_link():
    """Ensure an external link is rendered properly with a title that's formatted."""
    content = "[http://google.com ''foobar'']"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<p><a href="http://google.com"><i>foobar</i></a></p>'


def test_internal_link():
    """Ensure an internal link is rendered properly."""
    content = "[[Foobar]]"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<p><a href="/wiki/Foobar" title="Foobar">Foobar</a></p>'


def test_internal_link_title():
    """Ensure an internal link with a title is rendered properly."""
    content = "[[Foobar|fuzzbar]]"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<p><a href="/wiki/Foobar" title="Foobar">fuzzbar</a></p>'


def test_heading():
    """Test a heading."""
    content = "=== Foobar ==="
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<h3> Foobar </h3>'


def test_entity():
    """Test HTML entities."""
    content = "&Sigma; &#931; &#x3a3;"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<p>&Sigma; &#931; &#x3a3;</p>'


def test_entity_in_text():
    """Test entities appearing in text should be escaped."""
    content = "<test> &"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<p>&lt;test&gt; &amp;</p>'


@pytest.mark.skip('Not currently supported')
def test_preformatted():
    """Preformatted text should work properly."""
    content = " foo"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<pre>foo</pre>'


def test_unknown_node():
    """An unknown node type should raise an error."""
    with pytest.raises(UnknownNode):
        compose('')


def test_html():
    """Test a couple of HTML aspects."""
    content = "<hr></hr><hr/><hr /><a ></a >"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<hr /><hr /><hr /><hr /><a></a>"


def test_nowiki():
    """The contents of the nowiki tag should not be considered wiki."""
    content = "''<nowiki>'''Foo'''</nowiki>bar''"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<p><i>'''Foo'''bar</i></p>"


def test_invalid_resolver():
    """An unknown resolver type should raise an error."""
    with pytest.raises(ValueError):
        WikicodeToHtmlComposer(resolver='')
