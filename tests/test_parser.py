import mwparserfromhell

from mwcomposerfromhell import WikicodeToHtmlComposer


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


def test_template():
    """Render a content with a template."""
    content = "{{temp}}"
    template = "This is a test"
    # Create a composer and add the template to the cache.
    composer = WikicodeToHtmlComposer()
    composer._template_cache['temp'] = mwparserfromhell.parse(template)

    # Parse the main content.
    wikicode = mwparserfromhell.parse(content)
    result = composer.compose(wikicode)
    assert result == template


def test_template_with_args():
    """Render a content with a template that has arguments."""
    # Template that uses both a position and keyword argument.
    content = "{{temp|foobar|key=value}}"
    template = "This is a {{{1}}} {{{key}}}"
    # Create a composer and add the template to the cache.
    composer = WikicodeToHtmlComposer()
    composer._template_cache['temp'] = mwparserfromhell.parse(template)

    # Parse the main content.
    wikicode = mwparserfromhell.parse(content)
    result = composer.compose(wikicode)
    assert result == 'This is a foobar value'


def test_template_with_default():
    # Template that uses both a position (that isn't given, but has a default)
    # and keyword argument (that isn't given).
    content = "{{temp}}"
    template = "This is a '{{{1|}}}' {{{key}}}"
    # Create a composer and add the template to the cache.
    composer = WikicodeToHtmlComposer()
    composer._template_cache['temp'] = mwparserfromhell.parse(template)

    # Parse the main content.
    wikicode = mwparserfromhell.parse(content)
    result = composer.compose(wikicode)
    assert result == "This is a '' {{{key}}}"


def test_complex_template_name():
    """A template name that gets rendered via a different template."""
    # The name of the template is given by another template
    content = "{{t{{text|em}}p}}"
    # Create a composer and add the template to the cache.
    composer = WikicodeToHtmlComposer()
    composer._template_cache['text'] = mwparserfromhell.parse('{{{1}}}')
    composer._template_cache['temp'] = mwparserfromhell.parse('This is a test')

    # Parse the main content.
    wikicode = mwparserfromhell.parse(content)
    result = composer.compose(wikicode)
    assert result == 'This is a test'
