from io import StringIO

from mwcomposerfromhell.parser_tests_parser import (
    _parse_options,
    MediaWikiParserTestsParser,
)


def test_article():
    """Test parsing an article."""
    parser = MediaWikiParserTestsParser(
        StringIO(
            """!! article
Main Page
!! text
blah blah
!! endarticle
"""
        )
    )
    parser.parse()

    assert parser.articles == {"Main Page": "blah blah\n"}
    assert parser.test_cases == []


def test_comments():
    """Comments and blank lines outside of sections should be ignored."""
    parser = MediaWikiParserTestsParser(
        StringIO(
            """# This should be ignored.

!! article
Main Page
!! text
blah blah
!! endarticle
"""
        )
    )
    parser.parse()

    assert parser.articles == {"Main Page": "blah blah\n"}
    assert parser.test_cases == []


def test_test_case():
    """Comments and blank lines outside of sections should be ignored."""
    parser = MediaWikiParserTestsParser(
        StringIO(
            """!! test
Simple paragraph
!! wikitext
This is a simple paragraph.
!! html
<p>This is a simple paragraph.
</p>
!! end
"""
        )
    )
    parser.parse()

    assert parser.articles == {}
    assert parser.test_cases == [
        {
            "test": "Simple paragraph\n",
            "wikitext": "This is a simple paragraph.\n",
            "html": "<p>This is a simple paragraph.\n</p>\n",
            "options": {},
        }
    ]


def test_blank_test_case():
    """Comments and blank lines outside of sections should be ignored."""
    parser = MediaWikiParserTestsParser(
        StringIO(
            """!! test
Blank input
!! wikitext
!! html
!! end
"""
        )
    )
    parser.parse()

    assert parser.articles == {}
    assert parser.test_cases == [
        {
            "test": "Blank input\n",
            "wikitext": "",
            "html": "",
            "options": {},
        }
    ]


def test_parser_options():
    """An options section can exist."""
    parser = MediaWikiParserTestsParser(
        StringIO(
            """!! test
Options
!! wikitext
!! options
pst
!! html
!! end
"""
        )
    )
    parser.parse()

    assert parser.articles == {}
    assert parser.test_cases == [
        {
            "test": "Options\n",
            "wikitext": "",
            "options": {"pst": True},
            "html": "",
        }
    ]


def test_options():
    """An options section can exist."""
    result = _parse_options(
        """
pst
"""
    )
    assert result == {"pst": True}


def test_options_with_value():
    """An options section can exist."""
    result = _parse_options(
        """
thumbsize=0
language=en
"""
    )
    assert result == {"thumbsize": ["0"], "language": ["en"]}


def test_options_with_quoted_value():
    """Option values can be quoted to contain spaces."""
    result = _parse_options(
        """
test="foo bar"
"""
    )
    assert result == {"test": ["foo bar"]}


def test_options_with_multiple_values():
    """Each option can have multiple values (and they can have spaces around them)."""
    result = _parse_options(
        """
test=foo,bar
"""
    )
    assert result == {"test": ["foo", "bar"]}


def test_options_with_title():
    """An options section can exist."""
    result = _parse_options(
        """
title=[[Foo bar]]
"""
    )
    assert result == {"title": ["Foo bar"]}


def test_options_json():
    """Parsoid options can be JSON."""
    result = _parse_options(
        """
parsoid={ "modes": ["wt2html","wt2wt"], "normalizePhp": true }
"""
    )
    assert result == {
        "parsoid": [
            {
                "modes": ["wt2html", "wt2wt"],
                "normalizePhp": True,
            }
        ],
    }


def test_options_nested_json():
    result = _parse_options(
        """
parsoid={
  "modes": ["wt2wt", "selser"],
  "changes": [
    ["a", "contents", "text", "\\"-{"],
    ["td > span", "attr", "data-mw-variant", "{\\"disabled\\":{\\"t\\":\\"edited\\"}}"]
  ]
}
"""
    )
    assert result == {
        "parsoid": [
            {
                "modes": ["wt2wt", "selser"],
                "changes": [
                    ["a", "contents", "text", '"-{'],
                    [
                        "td > span",
                        "attr",
                        "data-mw-variant",
                        '{"disabled":{"t":"edited"}}',
                    ],
                ],
            }
        ],
    }


def test_option_spacing():
    """An options section can exist."""
    result = _parse_options(
        """
pst foo = bar, baz
"""
    )
    assert result == {
        "pst": True,
        "foo": ["bar", "baz"],
    }
