from pathlib import Path

import mwparserfromhell
import pytest

from mwcomposerfromhell import compose
from . import MediaWikiParserTestCasesParser

# Only a subset of tests pass right now.
WHITELIST = {
    "Blank input",
    "Simple paragraph",
    "Italics and possessives (2)",
    "Italics and bold: 2-quote opening sequence: (2,2)",
    "Italics and bold: 3-quote opening sequence: (3,3)",
    "Italics and bold: 5-quote opening sequence: (5,3+2)",
    "Italics and bold: 5-quote opening sequence: (5,5)",
    "Italics and bold: other quote tests: (2,3,5)",
    "Italics and bold: other quote tests: (2,(3,3),2)",
    "Italics and bold: other quote tests: (3,(2,2),3)",
    "Bare pipe character (T54363)",
    "T17491: <ins>/<del> in blockquote (2)",
    "<pre> with attributes (T5202)",
    "<pre> with width attribute (T5202)",
    "Entities inside <pre>",
    "HTML-pre: 2: indented text",
    "Link with 3 brackets",
    "Piped link with 3 brackets",
    "Link containing }",
    "Horizontal ruler -- <4 dashes render as plain text",
    "__proto__ is treated as normal wikitext (T105997)",
    "Table wikitext syntax outside wiki-tables",
    "div with no attributes",
    "div with double-quoted attribute",
    "Non-ASCII pseudo-tags are rendered as text",
    "text with amp in the middle of nowhere",
    "text with undefined character entity: xacute",
    "HTML tag with leading space is parsed as text",
    "Punctuation: CSS !important (T13874)",
    "HTML ordered list item with parameters oddity",
    "Correct handling of <td>, <tr> (T8171)",
    "Parsing crashing regression (fr:JavaScript)",
    "ISBN followed by 5 spaces",
    "ISBN with a dummy number",
    "ISBN with multiple spaces, no number",
    "Unclosed language converter markup \"-{\"",
    "new support for bdi element (T33817)",
}

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
    result = compose(wikicode)
    # TODO Removing trailing whitespace might not be correct here, but it
    #      shouldn't matter for HTML.
    assert result.rstrip() == html.rstrip()
