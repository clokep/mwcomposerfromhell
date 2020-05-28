from datetime import datetime

import mwparserfromhell

from mwcomposerfromhell import compose
from tests import patch_datetime

# Set the current time to a particular date.
patch_datetime_fixture = patch_datetime(datetime(2001, 8, 3, 9, 2, 3))


def pytest_generate_tests(metafunc):
    argnames = ('magic_word', 'output')
    argvalues = [
        ('YEAR', '2001'),
        ('MONTH', '08'),
        ('MONTH1', '8'),
        ('MONTHNAME', 'August'),
        ('MONTHABBREV', 'Aug'),
        ('DAY', '3'),
        ('DAY2', '03'),
        ('DOW', '5'),
        ('DAYNAME', 'Friday'),
        ('TIME', '09:02'),
        ('HOUR', '09'),
        ('WEEK', '32'),
        ('TIMESTAMP', '20010803090203'),
    ]
    # Generate both a current and local version of the tests.
    argvalues = [
        ('CURRENT' + magic_word, value) for (magic_word, value) in argvalues
    ] + [
        ('LOCAL' + magic_word, value) for (magic_word, value) in argvalues
    ]

    metafunc.parametrize(argnames, argvalues, ids=[v[0] for v in argvalues])


def test_magic_words(magic_word, output):
    """Test that simple formatting works."""
    content = "{{%s}}" % magic_word
    wikicode = mwparserfromhell.parse(content)
    assert compose(wikicode) == '<p>%s</p>' % output
