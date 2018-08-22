import mwparserfromhell

from mwcomposerfromhell import compose
from mwcomposerfromhell.composer import WikicodeToHtmlComposer


def test_simple():
    """Render a simple template."""
    # A simple template that's just a string.
    template = 'This is a test'
    template_store = {'temp': mwparserfromhell.parse(template)}

    # Parse the main content.
    wikicode = mwparserfromhell.parse('{{temp}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == template


def test_with_args():
    """Render a content with a template that has arguments."""
    # Template that uses both a position and keyword argument.
    template_store = {'temp': mwparserfromhell.parse('This is a "{{{1}}}" "{{{key}}}"')}

    # Parse the main content.
    wikicode = mwparserfromhell.parse('{{temp|foobar|key=value}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == 'This is a "foobar" "value"'


def test_with_default_args():
    """Render a template where arguments fall back to default values."""
    # Template that uses a position argument and a keyword argument, both with
    # defaults.
    template_store = {'temp': mwparserfromhell.parse('This is a "{{{1|first}}}" "{{{key|second}}}"')}

    # Parse the main content.
    wikicode = mwparserfromhell.parse('{{temp}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == 'This is a "first" "second"'


def test_with_blank_default_args():
    """Render a template where arguments fall back to blank values."""
    # Template that uses a position argument and a keyword argument, both with
    # blank defaults.
    template_store = {'temp': mwparserfromhell.parse('This is a "{{{1|}}}" "{{{key|}}}"')}

    # Parse the main content.
    wikicode = mwparserfromhell.parse('{{temp}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == 'This is a "" ""'


def test_without_default_args():
    """Render a template where arguments fall back to their keys."""
    # Template that uses a position argument and a keyword argument, without
    # defaults.
    template = 'This is a "{{{1}}}" "{{{key}}}"'
    template_store = {'temp': mwparserfromhell.parse(template)}

    # Parse the main content.
    wikicode = mwparserfromhell.parse('{{temp}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == template


def test_complex_name():
    """A template name that gets rendered via a different template."""
    template_store = {
        'text': mwparserfromhell.parse('{{{1}}}'),
        'temp': mwparserfromhell.parse('This is a test'),
    }

    # Parse the main content. The name of the template is given by another template
    wikicode = mwparserfromhell.parse('{{t{{text|em}}p}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == 'This is a test'


def test_complex_parameter_name():
    """A template name that gets rendered via a different template."""
    template_store = {
        'text': mwparserfromhell.parse('{{{1}}}'),
        'temp': mwparserfromhell.parse('This is a "{{{1}}}" "{{{key}}}"'),
    }

    # Parse the main content. The name of the template is given by another template
    wikicode = mwparserfromhell.parse('{{temp|first|k{{text|ey}}=second}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == 'This is a "first" "second"'


def test_complex_parameter_value():
    """A template name that gets rendered via a different template."""
    template_store = {
        'text': mwparserfromhell.parse('{{{1}}}'),
        'temp': mwparserfromhell.parse('This is a "{{{1}}}" "{{{key}}}"'),
    }

    # Parse the main content. The name of the template is given by another template
    wikicode = mwparserfromhell.parse('{{temp|fi{{text|rst}}|key={{text|sec}}ond}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == 'This is a "first" "second"'


def test_complex_arg():
    """An argument name gets generated in a complex fashion."""
    template_store = {
        'text': mwparserfromhell.parse('{{{1}}}'),
        'temp': mwparserfromhell.parse('This is a "{{{ {{text|1}} }}}" "{{{ {{text|key}} }}}"'),
    }

    # Parse the main content. The name of the template is given by another template
    wikicode = mwparserfromhell.parse('{{temp|first|key=second}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == 'This is a "first" "second"'


def test_spaces():
    """Spaces around a template name should be ignored."""
    # A simple template that's just a string.
    template = 'This is a test'
    template_store = {'temp': mwparserfromhell.parse(template)}

    # Parse the main content.
    wikicode = mwparserfromhell.parse('{{ temp }}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == template


def test_spaces_with_parameter():
    """Spaces around keyword parameters should be removed."""
    # Template that uses both a position and keyword argument.
    template_store = {'temp': mwparserfromhell.parse('This is a "{{{1}}}" "{{{key}}}"')}

    # Parse the main content.
    wikicode = mwparserfromhell.parse('{{temp| foobar | key = value}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == 'This is a " foobar " "value"'


def test_capitalization():
    """MediaWiki treats the first character as case-insensitive."""
    # A simple template that's just a string.
    template = 'This is a test'
    template_store = {'temp': mwparserfromhell.parse(template)}

    # Parse the main content.
    wikicode = mwparserfromhell.parse('{{Temp}}')

    # Render the result.
    composer = WikicodeToHtmlComposer(template_store=template_store)
    composer.compose(wikicode)
    assert composer.stream.getvalue() == template


def test_unknown():
    """An unknown template gets rendered as is."""
    content = '{{temp}}'
    wikicode = mwparserfromhell.parse(content)

    # Render the result.
    assert compose(wikicode) == content
