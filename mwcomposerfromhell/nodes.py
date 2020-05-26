from mwparserfromhell import nodes


class Wikilink(nodes.Wikilink):
    def __init__(self, title, text=None, trail=None):
        super().__init__(title, text)
        self.trail = trail

    @property
    def trail(self):
        """The link trail of the linked page, as a :class:`str`."""
        return self._trail

    @trail.setter
    def trail(self, value):
        self._trail = value
