from datetime import datetime
from typing import Callable, Dict, Union

# A magic word is a callable which takes two parameters (param and context) and
# returns a string.
MagicWord = Callable[[], str]

# The parameter for the formatting function generator.
_Format = Union[str, Callable[[datetime], str]]


def _datetime_field(fmt: _Format, utc: bool) -> MagicWord:
    """
    Generate a function which formats a datetime to a string.

    :param fmt: A format string, or a callable which has a single parameter (the
        ``datetime``) and returns a string.
    :param utc: Whether to return the date in UTC or local time.
    """

    def func() -> str:
        if utc:
            d = datetime.utcnow()
        else:
            d = datetime.now()

        if isinstance(fmt, str):
            return d.strftime(fmt)
        else:
            return fmt(d)

    return func


MAGIC_WORDS = {}

_FORMATTERS = {
    "YEAR": "%Y",  # Four-digit year
    "MONTH": "%m",  # Month (zero-padded)
    "MONTH1": "%-m",  # Month (unpadded)
    "MONTHNAME": "%B",  # Month (name)
    # This would not be correct in some languages.
    "MONTHNAMEGEN": "%B",  # Month (genitive form)
    "MONTHABBREV": "%b",  # Month (abbreviation)
    "DAY": "%-d",  # Day of the month (unpadded number)
    "DAY2": "%d",  # Day of the month (zero-padded number)
    "DOW": "%w",  # Day of the week (unpadded number), 0 (for Sunday) through 6 (for Saturday)
    "DAYNAME": "%A",  # Day of the week (name)
    "TIME": "%H:%M",  # Time (24-hour HH:mm format)
    "HOUR": "%H",  # Hour (24-hour zero-padded number)
    # datetime doesn't have a week parameter, and we need to start with 1, not 0.
    "WEEK": lambda d: str(int(d.strftime("%W")) + 1),  # Week (number)
    "TIMESTAMP": "%Y%m%d%H%M%S",  # YYYYMMDDHHmmss timestamp
}  # type: Dict[str, _Format]

for param, fmt in _FORMATTERS.items():
    MAGIC_WORDS["CURRENT" + param] = _datetime_field(fmt, True)
    MAGIC_WORDS["LOCAL" + param] = _datetime_field(fmt, False)
