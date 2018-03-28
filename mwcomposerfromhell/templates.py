"""
Handle MediaWiki Templates.
"""


class TemplateStore:
    """
    A template store maps template names (as strings) to
    mwparserfromhell.wikicode.Wikicode instances.

    """

    def __init__(self, templates=None, *args, **kwargs):
        super(TemplateStore, self).__init__(*args, **kwargs)

        if templates is None:
            templates = {}

        self.templates = templates

    def _clean_name(self, key):
        """MediaWiki treats the first character of article names as case-insensitive."""
        return key[0].lower() + key[1:]

    def __getitem__(self, key):
        return self.templates[self._clean_name(key)]

    def __setitem__(self, key, value):
        self.templates[self._clean_name(key)] = value
        return value
