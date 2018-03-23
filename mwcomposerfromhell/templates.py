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

    def __getitem__(self, key):
        return self.templates[key]

    def __setitem__(self, key, value):
        self.templates[key] = value
        return value
