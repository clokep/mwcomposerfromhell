from typing import Optional

from mwparserfromhell import nodes


class Wikilink(nodes.Wikilink):
    def __init__(
        self, title: str, text: Optional[str] = None, trail: Optional[str] = None
    ):
        super().__init__(title, text)
        self.trail = trail

    @property
    def trail(self) -> Optional[str]:
        """The link trail of the linked page, as a :class:`str`."""
        return self._trail

    @trail.setter
    def trail(self, value: Optional[str]) -> None:
        self._trail = value
