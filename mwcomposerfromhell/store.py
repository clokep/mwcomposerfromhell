import json
import re

import mwparserfromhell


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
        key = key.strip()
        return self.templates[key]

    def __setitem__(self, key, value):
        key = key.strip()
        self.templates[key] = value
        return value
