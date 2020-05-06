"""
Handle MediaWiki Templates.
"""
from typing import Any, Dict


class TemplateStore:
    """
    A template store maps template names (as strings) to
    mwparserfromhell.wikicode.Wikicode instances.

    """

    def __init__(self, templates: Dict[str, Any] = None):
        if templates is None:
            templates = {}

        self.templates = templates

    def _clean_name(self, key: str) -> str:
        """MediaWiki treats the first character of article names as case-insensitive."""
        return key[0].lower() + key[1:]

    def __getitem__(self, key: str) -> Any:
        return self.templates[self._clean_name(key)]

    def __setitem__(self, key: str, value: Any) -> Any:
        self.templates[self._clean_name(key)] = value
        return value
