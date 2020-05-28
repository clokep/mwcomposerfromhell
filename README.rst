mwcomposerfromhell
##################

.. image:: https://travis-ci.org/clokep/mwcomposerfromhell.svg?branch=master
    :target: https://travis-ci.org/clokep/mwcomposerfromhell

**mwcomposerfromhell** is a Python package that provides an easy-to-use method
to convert MediaWiki `Wikicode`_ to HTML via `mwparserfromhell`_. It supports
Python 3.

.. _Wikicode: https://en.wikipedia.org/wiki/Help:Wikitext
.. _mwparserfromhell: https://mwparserfromhell.readthedocs.io

Usage
-----

Normal usage is rather straightforward to convert from a ``str`` of Wikicode to
a ``str`` of HTML. It involves two steps:

1. Parse the Wikicode to an abstract syntax tree using ``mwparserfromhell``.
2. Convert the AST to HTML.

.. code-block:: python

    >>> import mwparserfromhell
    >>> import mwcomposerfromhell
    >>> wikicode = mwparserfromhell.parse(text)  # Step 1
    >>> html = mwcomposerfromhell.compose(wikicode)  # Step 2

You can also use it from the command line if you already have your wikicode in
a file. The convert HTML is output on standard out.

.. code-block:: sh

    python -m mwcomposerfromhell path/to/my/wikicode
