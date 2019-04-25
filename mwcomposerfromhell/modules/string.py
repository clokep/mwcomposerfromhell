"""
This module is intended to provide access to basic string functions.

Most of the functions provided here can be invoked with named parameters,
unnamed parameters, or a mixture. If named parameters are used, Mediawiki will
automatically remove any leading or trailing whitespace from the parameter.
Depending on the intended use, it may be advantageous to either preserve or
remove such whitespace.

See https://en.wikipedia.org/wiki/Module:String

"""
# Store the Python version so it isn't shadowed.
_len = len


def len(context):  # noqa: A001
    try:
        s = context['s']
    except KeyError:
        s = context.get('1', '')
    return str(_len(s))
