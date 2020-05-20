from pathlib import Path

import mwparserfromhell
import pytest

from mwcomposerfromhell import WikicodeToHtmlComposer
from . import MediaWikiParserTestCasesParser

# Only a subset of tests pass right now.
with open(Path(__file__).parent / 'whitelist.txt') as f:
    WHITELIST = set([l.strip() for l in f])

# Whether to only run the tests above or to run them all and skip failing tests.
ONLY_RUN_WHITELIST = False

# Some tests have a standard HTML output, while others differ based on the
# parser. Prefer the standard output, then the PHP parser's.
PREFERRED_HTML = ('html', 'html/*', 'html/php')
# A known object.
_SENTINEL = object()


def pytest_generate_tests(metafunc):
    """Auto-generate test cases from parserTests.txt."""
    with open(Path(__file__).parent.joinpath('parserTests.txt')) as f:
        parser = MediaWikiParserTestCasesParser(f)
        parser.parse()

    argnames = ('wikitext', 'html', 'templates', 'skip', 'expected_pass')

    # For now only care about templates.
    templates = {}
    for article_name, article_contents in parser.articles.items():
        if not article_name.startswith('Template:'):
            continue

        templates[article_name[len('Template:'):]] = mwparserfromhell.parse(article_contents)

    # Pull out the necessary info for the tests.
    test_ids = []
    argvalues = []
    for test_case in parser.test_cases:
        # Find the best matching output from this test.
        html = _SENTINEL
        for html_section in PREFERRED_HTML:
            html = test_case.get(html_section, _SENTINEL)
            if html is not _SENTINEL:
                break

        # Ignore tests without HTML.
        if html is _SENTINEL:
            continue

        # Use the test name as the ID.
        test_id = test_case['test'].strip()

        # Whether the test is expected to pass.
        expected_pass = test_id in WHITELIST

        # Sometimes it is useful to only run the whitelisted tests.
        if ONLY_RUN_WHITELIST and not expected_pass:
            continue

        test_ids.append(test_id)

        # Skip some tests based on their options.
        options = test_case.get('options', {})
        skip = 'pst' in options or 'msg' in options

        # Add the current test arguments to the list of values.
        argvalues.append(
            (test_case['wikitext'], html, templates, skip, expected_pass)
        )

    metafunc.parametrize(argnames, argvalues, ids=test_ids)


def test_parser_tests(wikitext, html, templates, skip, expected_pass):
    """Handle an individual parser test from parserTests.txt."""
    if skip:
        pytest.skip('Skipping test')
    if not expected_pass:
        pytest.xfail('Expected fail')

    # Parse the incoming article.
    wikicode = mwparserfromhell.parse(wikitext)

    # Generate the composer with the current templates.
    composer = WikicodeToHtmlComposer(base_url='/wiki', template_store=templates)
    # Convert the wikicode to HTML.
    result = composer.compose(wikicode)

    # TODO Removing trailing whitespace might not be correct here, but it
    #      shouldn't matter for HTML.
    assert result.rstrip() == html.rstrip()
