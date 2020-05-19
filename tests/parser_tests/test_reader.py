from io import StringIO

from . import MediaWikiParserTestCasesParser


def test_article():
    """Test parsing an article."""
    parser = MediaWikiParserTestCasesParser(StringIO("""!! article
Main Page
!! text
blah blah
!! endarticle
"""))
    parser.parse()

    assert parser.articles == {'Main Page': 'blah blah\n'}
    assert parser.test_cases == []


def test_comments():
    """Comments and blank lines outside of sections should be ignored."""
    parser = MediaWikiParserTestCasesParser(StringIO("""# This should be ignored.

!! article
Main Page
!! text
blah blah
!! endarticle
"""))
    parser.parse()

    assert parser.articles == {'Main Page': 'blah blah\n'}
    assert parser.test_cases == []


def test_test_case():
    """Comments and blank lines outside of sections should be ignored."""
    parser = MediaWikiParserTestCasesParser(StringIO("""!! test
Simple paragraph
!! wikitext
This is a simple paragraph.
!! html
<p>This is a simple paragraph.
</p>
!! end
"""))
    parser.parse()

    assert parser.articles == {}
    assert parser.test_cases == [{
        'test': 'Simple paragraph\n',
        'wikitext': 'This is a simple paragraph.\n',
        'html': '<p>This is a simple paragraph.\n</p>\n',
    }]


def test_blank_test_case():
    """Comments and blank lines outside of sections should be ignored."""
    parser = MediaWikiParserTestCasesParser(StringIO("""!! test
Blank input
!! wikitext
!! html
!! end
"""))
    parser.parse()

    assert parser.articles == {}
    assert parser.test_cases == [{
        'test': 'Blank input\n',
        'wikitext': '',
        'html': '',
    }]
