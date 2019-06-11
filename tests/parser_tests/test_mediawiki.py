from io import StringIO

import mwparserfromhell

from mwcomposerfromhell import compose
from . import MediaWikiParserTestCasesParser


def pytest_generate_tests(metafunc):
    """Auto-generate test cases from parserTests.txt."""
    parser = MediaWikiParserTestCasesParser(StringIO("""!! test
Blank input
!! wikitext
!! html
!! end
"""))
    parser.parse()

    argnames = ['wikitext', 'html']
    # Use the test name as the ID.
    ids = list(map(lambda d: d['test'].strip(), parser.test_cases))
    # Pull out the wikitext and expected HTML.
    # TODO Handle different HTML types.
    argvalues = map(lambda d: (d['wikitext'], d['html']), parser.test_cases)

    metafunc.parametrize(argnames, argvalues, ids=ids)


def test_parser_tests(wikitext, html):
    """Handle an individual parser test from parserTests.txt."""
    wikicode = mwparserfromhell.parse(wikitext)
    assert compose(wikicode) == html
