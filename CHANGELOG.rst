Changelog
#########

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
