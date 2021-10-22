from datetime import datetime

import mwparserfromhell
import pytest

from mwcomposerfromhell import compose
from tests import patch_datetime

# Set the current time to a particular date.
patch_datetime_fixture = patch_datetime(datetime(2001, 8, 3, 9, 2, 3))


_argvalues = [
    ("YEAR", "2001"),
    ("MONTH", "08"),
    ("MONTH1", "8"),
    ("MONTHNAME", "August"),
    ("MONTHABBREV", "Aug"),
    ("DAY", "3"),
    ("DAY2", "03"),
    ("DOW", "5"),
    ("DAYNAME", "Friday"),
    ("TIME", "09:02"),
    ("HOUR", "09"),
    ("WEEK", "32"),
    ("TIMESTAMP", "20010803090203"),
]


@pytest.mark.parametrize(
    ("magic_word", "output"),
    # Generate both a current and local version of the tests.
    [("CURRENT" + magic_word, value) for (magic_word, value) in _argvalues]
    + [("LOCAL" + magic_word, value) for (magic_word, value) in _argvalues],
)
def test_magic_words(magic_word, output):
    """Test that simple formatting works."""
    content = "{{%s}}" % magic_word
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == f"<p>{output}</p>"


def test_case_sensitivty():
    """Magic words are case-sensitive."""
    content = "{{currentyear}}"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<p>{{currentyear}}</p>"


def test_params():
    """Parameters get discarded."""
    content = "{{CURRENTYEAR|foo}}"
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == "<p>2001</p>"
