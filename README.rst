mwcomposerfromhell
##################

.. image:: https://travis-ci.org/clokep/mwcomposerfromhell.svg?branch=master
    :target: https://travis-ci.org/clokep/mwcomposerfromhell

**mwcomposerfromhell** is a Python package that provides an easy-to-use composer
to convert the MediaWiki `Wikicode`_ to HTML via `mwparserfromhell`_. It supports
Python 3.

.. _Wikicode: https://en.wikipedia.org/wiki/Help:Wikitext
.. _mwparserfromhell: https://mwparserfromhell.readthedocs.io

Usage
-----

Normal usage is rather straightforward (where ``text`` is page text)

.. code-block:: python

    >>> import mwparserfromhell
    >>> import mwcomposerfromhell
    >>> wikicode = mwparserfromhell.parse(text)
    >>> html = mwcomposerfromhell.compose(wikicode)

``html`` is a ``str`` object for the output HTML.
