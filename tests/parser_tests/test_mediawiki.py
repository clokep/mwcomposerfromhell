from pathlib import Path

import mwparserfromhell

from mwcomposerfromhell import compose
from . import MediaWikiParserTestCasesParser


def pytest_generate_tests(metafunc):
    """Auto-generate test cases from parserTests.txt."""
    with open(Path(__file__).parent.joinpath('parserTests.txt')) as f:
        parser = MediaWikiParserTestCasesParser(f)
        parser.parse()

    argnames = ['wikitext', 'html']
    # Ignore tests without HTML.
    test_cases = list(filter(lambda t: 'html' in t, parser.test_cases))
    # Use the test name as the ID.
    ids = list(map(lambda t: t['test'].strip(), test_cases))
    # Pull out the wikitext and expected HTML.
    # TODO Handle different HTML types.
    argvalues = map(lambda d: (d['wikitext'], d['html']), test_cases)

    metafunc.parametrize(argnames, argvalues, ids=ids)


def test_parser_tests(wikitext, html):
    """Handle an individual parser test from parserTests.txt."""
    wikicode = mwparserfromhell.parse(wikitext)
    assert compose(wikicode) == html
