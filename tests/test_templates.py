import mwparserfromhell

from mwcomposerfromhell.composer import WikicodeToHtmlComposer


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
