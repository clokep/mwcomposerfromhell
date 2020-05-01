from pathlib import Path

import mwparserfromhell

import pytest

from mwcomposerfromhell import compose
from . import MediaWikiParserTestCasesParser

# Only a subset of tests pass right now.
WHITELIST = {
    "Blank input",
    "T17491: <ins>/<del> in blockquote (2)",
    "<pre> with attributes (T5202)",
    "<pre> with width attribute (T5202)",
    "Entities inside <pre>",
    "HTML-pre: 2: indented text",
    "div with no attributes",
    "div with double-quoted attribute",
    "Expansion of multi-line templates in attribute values (T8255 sanity check 2)",
    "Punctuation: CSS !important (T13874)",
    "HTML ordered list item with parameters oddity",
    "Correct handling of <td>, <tr> (T8171)",
    "new support for bdi element (T33817)",
}


def pytest_generate_tests(metafunc):
    """Auto-generate test cases from parserTests.txt."""
    with open(Path(__file__).parent.joinpath('parserTests.txt')) as f:
        parser = MediaWikiParserTestCasesParser(f)
        parser.parse()

    argnames = ['wikitext', 'html', 'expected_pass']

    # Pull out the necessary info for the tests.
    ids = []
    argvalues = []
    for test_case in parser.test_cases:
        # Ignore tests without HTML.
        if 'html' not in test_case:
            continue

        # Use the test name as the ID.
        id = test_case['test'].strip()
        ids.append(id)

        # Pull out the wikitext and expected HTML.
        # TODO Handle different HTML types.
        argvalues.append(
            (test_case['wikitext'], test_case['html'], id in WHITELIST)
        )

    metafunc.parametrize(argnames, argvalues, ids=ids)


def test_parser_tests(wikitext, html, expected_pass):
    """Handle an individual parser test from parserTests.txt."""
    if not expected_pass:
        pytest.xfail("Expected fail")

    wikicode = mwparserfromhell.parse(wikitext)
    assert compose(wikicode) == html
