Changelog
#########

next
====

* Remove the "module" infrastructure and implement parser functions as a
  replacement. This is not a 1-to-1 replacement, as ``#invoke`` is not
  implemented, but the APIs now exist in a sane way to implement any parser
  function.
* Basic support for ``subst`` and ``safesubst``.
* Add a ``mwcomposerfromhell.parser_tests_parser`` module to read MediaWiki
  parser test files.
* Various internal improvements, including type hints and f-strings.
* Changed packaging to use setuptools declarative config in `setup.cfg`.

0.4 (May 29, 2020)
==================

.. warning::

  The constructor to ``WikicodeToHtmlComposer`` has changed to support articles
  in multiple namespaces. Be sure to adapt your code if you're instantiating
  a composer directly.

* Article resolution was modified and is now handled in a separate base class.
  As part of this, the default base URL was changed to ``/wiki``.
* Basic support for magic words.
* Better handling of text surrounding comment tags.
* Handling of article content outside of the ``Template`` namespace is supported.
* Ensure there isn't an infinite loop in template transclusion.
* Partially support rendering of edit links.
* Properly handle ``nowiki``, ``includeonly``, and `noinclude`` tags.
* Support link trails (e.g. ``[[Foo]]bar``).
* More accurate table rendering.
* Support for handling preformatted text (in the body or in a ``pre`` tag).
* The ``mwcomposerfromhell`` module can now run as a module to convert a file.
* Do not render raw ``a`` tags.

0.3 (May 21, 2020)
==================

* Fix escaping HTML entities in text (e.g. convert ``<`` to ``&lt;``).
* Handling of paragraphs and multiple line breaks has been greatly improved.
* Links now include a ``title`` attribute and are properly capitalized.
* Properly handle self-closing tags (e.g. ``<hr />``).
* Descriptions lists with details are properly handled.
* Comments are ignored instead of propagating them to the output.
* The composer no longer supports a streaming interface.
* Basic type hints are included.

0.2.1 (June 26, 2019)
=====================

* Stop modifying the mwparserfromhell library.
* Remove obsolete methods to directly handle a ``list`` or ``tuple`` in the
  ``WikicodeToHtmlComposer``
* Fix bugs with rendering templates:

  * Default arguments can now use other argument replacements.
  * Arguments are now properly replaced in wikilink and external links.

0.2 (May 8, 2019)
=================

* Add support for the Header and Attribute nodes.
* ``WikicodeToHtmlComposer`` optionally supports a output stream. Calling
  ``compose()`` no longer returns the string directly.
* Support attributes for ``Tag`` nodes.
* Many bugs fixed (in particular around complex lists and tables).

0.1 (March 28, 2018)
====================

* Basic support for converting parsed MediaWiki wikicode to HTML.
