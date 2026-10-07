from mwparserfromhell import nodes


class Wikilink(nodes.Wikilink):
    def __init__(self, title: str, text: str | None = None, trail: str | None = None):
        super().__init__(title, text)
        self.trail = trail

    @property
    def trail(self) -> str | None:
        """The link trail of the linked page, as a :class:`str`."""
        return self._trail

    @trail.setter
    def trail(self, value: str | None) -> None:
        self._trail = value
