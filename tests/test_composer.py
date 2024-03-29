import mwparserfromhell
import pytest

from mwcomposerfromhell import compose, WikicodeToHtmlComposer
from mwcomposerfromhell.composer import UnknownNode


def test_formatting():
    """Test that simple formatting works."""
    content = "''foobar''"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<p><i>foobar</i></p>"


def test_formatting_link():
    """Ensure an external link is rendered properly with a title that's formatted."""
    content = "[http://google.com ''foobar'']"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<p><a href="http://google.com"><i>foobar</i></a></p>'


def test_internal_link():
    """Ensure an internal link is rendered properly."""
    content = "[[Foobar]]"
    wikicode = mwparserfromhell.parse(content)
    assert (
        compose(wikicode) == '<p><a href="/wiki/Foobar" title="Foobar">Foobar</a></p>'
    )


def test_internal_link_text():
    """Ensure an internal link with text is rendered properly."""
    content = "[[Foobar|fuzzbar]]"
    wikicode = mwparserfromhell.parse(content)
    assert (
        compose(wikicode) == '<p><a href="/wiki/Foobar" title="Foobar">fuzzbar</a></p>'
    )


def test_link_trail():
    """Ensure an internal link with trail is rendered properly."""
    content = "[[Foo]]bar"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<p><a href="/wiki/Foo" title="Foo">Foobar</a></p>'


def test_link_trail_text():
    """Ensure an internal link with trail and text is rendered properly."""
    content = "[[Foo|foo]]bar"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<p><a href="/wiki/Foo" title="Foo">foobar</a></p>'


def test_heading():
    """Test a heading."""
    content = "=== Foobar ==="
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<h3> Foobar </h3>"


def test_entity():
    """Test HTML entities."""
    content = "&Sigma; &#931; &#x3a3;"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<p>&Sigma; &#931; &#x3a3;</p>"


def test_entity_in_text():
    """Test entities appearing in text should be escaped."""
    content = "<test> &"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<p>&lt;test&gt; &amp;</p>"


def test_preformatted():
    """Preformatted text should work properly."""
    content = " foo"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<pre>foo</pre>\n"


def test_preformatted_complicated():
    """ """
    # Note the lines with just spaces on them.
    content = "foo\n \n \n \n  bar\n\n baz\n"
    wikicode = mwparserfromhell.parse(content)
    assert (
        compose(wikicode)
        == "<p>foo\n</p><p><br />\n</p><pre> bar\n</pre>\n<pre>baz\n</pre>\n"
    )


def test_pre():
    """pre is similar to nowiki"""
    content = """<pre><!--Comment-->

[[wiki]] markup &amp;</pre>"""
    wikicode = mwparserfromhell.parse(content)
    assert (
        compose(wikicode)
        == """<pre>&lt;!--Comment--&gt;

[[wiki]] markup &amp;</pre>"""
    )


def test_unknown_node():
    """An unknown node type should raise an error."""
    with pytest.raises(UnknownNode):
        compose("")


def test_html():
    """Test a couple of HTML aspects."""
    content = "<hr></hr><hr/><hr /><i ></i >"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<hr /><hr /><hr /><hr /><p><i></i></p>"


def test_html_a():
    """Anchor tags are not alloewd."""
    content = '<a href="foo">&bar&amp;</a>'
    wikicode = mwparserfromhell.parse(content)
    assert (
        compose(wikicode)
        == "<p>&lt;a href=&quot;foo&quot;&gt;&amp;bar&amp;&lt;/a&gt;</p>"
    )


def test_nowiki():
    """The contents of the nowiki tag should not be considered wiki."""
    content = "''<nowiki>'''Foo'''</nowiki>bar''"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<p><i>'''Foo'''bar</i></p>"


def test_invalid_resolver():
    """An unknown resolver type should raise an error."""
    with pytest.raises(ValueError):
        WikicodeToHtmlComposer(resolver="")
