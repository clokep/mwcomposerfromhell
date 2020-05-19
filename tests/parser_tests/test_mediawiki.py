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


def pytest_generate_tests(metafunc):
    """Auto-generate test cases from parserTests.txt."""
    with open(Path(__file__).parent.joinpath('parserTests.txt')) as f:
        parser = MediaWikiParserTestCasesParser(f)
        parser.parse()

    argnames = ['wikitext', 'html', 'expected_pass']

    # Pull out the necessary info for the tests.
    test_ids = []
    argvalues = []
    for test_case in parser.test_cases:
        # Ignore tests without HTML.
        if 'html' not in test_case:
            continue

        # Use the test name as the ID.
        test_id = test_case['test'].strip()

        # Whether the test is expected to pass.
        expected_pass = test_id in WHITELIST

        # Sometimes it is useful to only run the whitelisted tests.
        if ONLY_RUN_WHITELIST and not expected_pass:
            continue

        test_ids.append(test_id)

        # Pull out the wikitext and expected HTML.
        # TODO Handle different HTML types.
        argvalues.append(
            (test_case['wikitext'], test_case['html'], expected_pass)
        )

    metafunc.parametrize(argnames, argvalues, ids=test_ids)


def test_parser_tests(wikitext, html, expected_pass):
    """Handle an individual parser test from parserTests.txt."""
    if not expected_pass:
        pytest.xfail("Expected fail")

    wikicode = mwparserfromhell.parse(wikitext)

    composer = WikicodeToHtmlComposer(base_url='/wiki')
    result = composer.compose(wikicode)

    # TODO Removing trailing whitespace might not be correct here, but it
    #      shouldn't matter for HTML.
    assert result.rstrip() == html.rstrip()
