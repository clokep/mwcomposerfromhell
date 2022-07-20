from collections import defaultdict
from datetime import datetime
from os import environ
from pathlib import Path

import mwparserfromhell
import pytest

from mwcomposerfromhell import ArticleResolver, Namespace, WikicodeToHtmlComposer
from mwcomposerfromhell.parser_tests_parser import MediaWikiParserTestsParser
from tests import patch_datetime

# Only a subset of tests pass right now.
with open(Path(__file__).parent / "whitelist.txt") as f:
    WHITELIST = {line.strip() for line in f}

# Whether to only run the tests above or to run them all and skip failing tests.
ONLY_RUN_WHITELIST = environ.get("ONLY_RUN_WHITELIST") is not None

# Some tests have a standard HTML output, while others differ based on the
# parser. Prefer the standard output, then the PHP parser's.
PREFERRED_HTML = (
    "html",
    "html+tidy",
    "html/*",
    "html/php",
    "html/php+tidy",
    "html/parsoid",
)
# A known object.
_SENTINEL = object()

# Set the current time to a particular date.
patch_datetime_fixture = patch_datetime(datetime(1970, 1, 1, 0, 2, 3))


def pytest_generate_tests(metafunc):
    """Auto-generate test cases from parserTests.txt."""
    with open(Path(__file__).parent.joinpath("parserTests.txt")) as f:
        parser = MediaWikiParserTestsParser(f)
        parser.parse()

    # The arguments that will be passed into each test case.
    argnames = ("wikitext", "html", "resolver", "options", "expected_pass")

    # Namespace -> {Article name -> contents}
    namespaces = defaultdict(Namespace)
    for article_name, article_contents in parser.articles.items():
        namespace, _, article_name = article_name.partition(":")
        # If there's no name, it means that it is in the main namespace.
        if not article_name:
            article_name = namespace
            namespace = ""

        # The articles are inconsistent about what the case of the MediaWiki
        # namespace. Hard-code it.
        if namespace.lower() == "mediawiki":
            namespace = "MediaWiki"

        namespaces[namespace][article_name] = mwparserfromhell.parse(article_contents)
    resolver = ArticleResolver("/wiki/", "/index.php")
    for namespace_name, namespace in namespaces.items():
        resolver.add_namespace(namespace_name, namespace)

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
        test_id = test_case["test"].strip()

        # Whether the test is expected to pass.
        expected_pass = test_id in WHITELIST

        # Sometimes it is useful to only run the whitelisted tests.
        if ONLY_RUN_WHITELIST and not expected_pass:
            continue

        test_ids.append(test_id)

        # Some tests don't have options.
        options = test_case.get("options", {})

        # Add the current test arguments to the list of values.
        argvalues.append(
            (test_case["wikitext"], html, resolver, options, expected_pass)
        )

    metafunc.parametrize(argnames, argvalues, ids=test_ids)


def test_parser_tests(wikitext, html, resolver, options, expected_pass):
    """Handle an individual parser test from parserTests.txt."""
    if "disable" in options:
        pytest.skip("Skipping test")

    # Parse the incoming article.
    wikicode = mwparserfromhell.parse(wikitext)

    # Generate the composer with the current templates.
    composer = WikicodeToHtmlComposer(
        resolver=resolver,
        red_links=True,
        expand_templates="pst" not in options,
    )
    # Convert the wikicode to HTML.
    result = composer.compose(wikicode)

    # Print out the results for comparison if the test fails.
    print(repr(result))
    print(repr(html))

    try:
        # Remove trailing whitespace for comparison.
        assert result.strip() == html.strip()
    except AssertionError:
        if not expected_pass:
            pytest.xfail("Expected fail")
        raise
