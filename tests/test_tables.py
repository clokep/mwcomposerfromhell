import mwparserfromhell

from mwcomposerfromhell import compose

def test_table():
    """Test an wiki table."""
    content = """{|
|-
! Header 1 !! Header 2 !! Header 3
|-
| Example 1a || Example 2a || Example 3a
|-
| Example 1b || Example 2b || Example 3b
|}"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == """<table><tr><th> Header 1 </th><th> Header 2 </th><th> Header 3
</th></tr><tr><td> Example 1a </td><td> Example 2a </td><td> Example 3a
</td></tr><tr><td> Example 1b </td><td> Example 2b </td><td> Example 3b
</td></tr></table>"""


def test_table_class():
    """Test an wiki table."""
    content = """{| class="wikitable"
|-
! Header 1 !! Header 2
|-
| Example 1 || Example 2
|}"""
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == """<table class="wikitable"><tr><th> Header 1 </th><th> Header 2
</th></tr><tr><td> Example 1 </td><td> Example 2
</td></tr></table>"""
