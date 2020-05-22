from datetime import datetime
from typing import Callable


def _datetime_field(fmt: str, utc: bool) -> Callable[[], str]:
    """Generate a function which formats a datetime to a string."""
    def func():
        if utc:
            d = datetime.utcnow()
        else:
            d = datetime.now()
        return d.strftime(fmt)
    return func


MAGIC_WORDS = {}

_FORMATTERS = {
    'YEAR': '%Y',  # Four-digit year
    'MONTH': '%m',  # Month (zero-padded)
    'MONTH1': '%-m',  # Month (unpadded)
    'MONTHNAME': '%B',  # Month (name)
    # TODO
    # 'MONTHNAMEGEN': '',  # Month (genitive form)
    'MONTHABBREV': '%b',  # Month (abbreviation)
    'DAY': '%-d',  # Day of the month (unpadded number)
    'DAY2': '%d',  # Day of the month (zero-padded number)
    'DOW': '%w',  # Day of the week (unpadded number), 0 (for Sunday) through 6 (for Saturday)
    'DAYNAME': '%A',  # Day of the week (name)
    'TIME': '%H:%M',  # Time (24-hour HH:mm format)
    'HOUR': '%H',  # Hour (24-hour zero-padded number)
    'WEEK': '%U',  # Week (number)
    'TIMESTAMP': '%Y%m%d%H%M%S',  # YYYYMMDDHHmmss timestamp
}

for param, fmt in _FORMATTERS.items():
    MAGIC_WORDS['CURRENT' + param] = _datetime_field(fmt, True)
    MAGIC_WORDS['LOCAL' + param] = _datetime_field(fmt, False)
