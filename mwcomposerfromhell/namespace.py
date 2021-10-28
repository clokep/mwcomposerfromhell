import html
import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote, unquote, urlencode

from mwparserfromhell.wikicode import Wikicode

from mwcomposerfromhell.magic_words import MAGIC_WORDS, MagicWord


# A parser function is a callable which takes two parameters (param and context)
# and returns a string to replace itself with.
Context = List[Tuple[str, str, bool]]
ParentContext = Dict[str, str]
ParserFunction = Callable[[str, Context, ParentContext], str]

MULTIPLE_SPACES = re.compile(r" +")


class ArticleNotFound(Exception):
    """The article was not found."""


class MagicWordNotFound(Exception):
    """The magic word does not exist."""


class ParserFunctionNotFound(Exception):
    """The parser function does not exist."""


class CanonicalTitle:
    def __init__(self, namespace: str, title: str, interwiki: str):
        self.namespace = namespace
        self.title = title
        self.interwiki = interwiki

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CanonicalTitle):
            return False

        return (self.namespace, self.title, self.interwiki) == (
            other.namespace,
            other.title,
            other.interwiki,
        )

    @property
    def full_title(self) -> str:
        if self.namespace:
            return self.namespace + ":" + self.title
        else:
            return self.title

    @property
    def link(self) -> str:
        """Get a version of the canonical title appropriate for a URL."""
        return self.full_title.replace(" ", "_")


def _normalize_spaces(key: str) -> str:
    """Spaces are turned to underscores, multiple get combined, and stripped from the beginning and end."""
    # Convert spaces to underscores.
    key = key.replace("_", " ")
    # Replace strings of underscores with a single underscore.
    key = MULTIPLE_SPACES.sub(" ", key)
    # Remove all underscores from the start and end.
    return key.strip("_")


def _normalize_namespace(key: str) -> str:
    """MediaWiki treats the first character of namespaces as upper-case and the rest as lower-case."""
    if not key:
        return ""
    key = _normalize_spaces(key)
    return key[0].upper() + key[1:].lower()


def _normalize_title(key: str) -> str:
    """MediaWiki treats the first character of article names as upper-case."""
    if not key:  # Empty string
        return ""
    key = _normalize_spaces(key)
    return key[0].upper() + key[1:]


class Namespace:
    """
    A Namespace maps article names (as strings) to
    ``mwparserfromhell.wikicode.Wikicode`` instances.

    Note that each article is expected to already have the namespace name removed.
    """

    def __init__(self, articles: Optional[Dict[str, Wikicode]] = None):
        if articles is None:
            self._articles = {}
        else:
            # Fix the names of any incoming articles.
            self._articles = {
                _normalize_title(name): article for name, article in articles.items()
            }

    def __getitem__(self, key: str) -> Wikicode:
        return self._articles[_normalize_title(key)]

    def __setitem__(self, key: str, value: Wikicode) -> Wikicode:
        self._articles[_normalize_title(key)] = value
        return value


class ArticleResolver:
    """
    Holds the configuration of things that can be referenced from articles.
    """

    def __init__(self, base_url: str = "/wiki/", edit_url: str = "/index.php"):
        # The base URL should be the root that articles sit in.
        self._base_url = base_url.rstrip("/")
        self._edit_url = edit_url

        # A map of namespace names to Namespace objects. Used to find articles.
        self._namespaces = {}  # type: Dict[str, Namespace]
        # A map of the "canonical" namespace to the "human" capitalization.
        self._canonical_namespaces = {}  # type: Dict[str, str]

        # A map of magic words to callables.
        self._magic_words = MAGIC_WORDS.copy()  # type: Dict[str, MagicWord]

        # A map of parser functions to callable.
        self._parser_functions = {}  # type: Dict[str, ParserFunction]

    def add_namespace(self, name: str, namespace: Namespace) -> None:
        self._namespaces[_normalize_namespace(name)] = namespace
        self._canonical_namespaces[_normalize_namespace(name)] = name

    def get_article_url(self, canonical_title: CanonicalTitle) -> str:
        """Given a canonical title, return a URL suitable for linking."""
        # TODO Handle interwiki links.
        title = quote(canonical_title.link, safe="/:~")
        return f"{self._base_url}/{title}"

    def get_edit_url(self, canonical_title: CanonicalTitle) -> str:
        """Given a page title, return a URL suitable for editing that page."""
        params = (
            ("title", canonical_title.link),
            ("action", "edit"),
            ("redlink", "1"),
        )
        # MediaWiki generates an escaped URL.
        return "{}?{}".format(self._edit_url, html.escape(urlencode(params, safe=":")))

    def resolve_article(self, name: str, default_namespace: str) -> CanonicalTitle:
        """
        Get the canonical namespace and name for an article.

        :param name: The name of the article to find.
        :param default_namespace: The namespace to use, if one is not provided.
        """
        return self.canonicalize_title(name, default_namespace)

    def get_article(self, name: str, default_namespace: str = "") -> Wikicode:
        """
        Get an article's content (as ``mwparserfromhell.wikicode.Wikicode``) from a name.

        :param name: The name of the article to find.
        :param default_namespace: The namespace to use, if one is not provided.
        """
        canonical_title = self.resolve_article(name, default_namespace)

        try:
            return self._namespaces[canonical_title.namespace][canonical_title.title]
        except KeyError:
            raise ArticleNotFound(canonical_title)

    def canonicalize_title(
        self, title: str, default_namespace: str = ""
    ) -> CanonicalTitle:
        """
        Generate the canonical form of a title.

        See https://en.wikipedia.org/wiki/Help:Link#Conversion_to_canonical_form

        TODO Handle anonymous user pages.
        """
        # HTML entities and percent encoded characters get converted to their raw
        # character.
        title = html.unescape(unquote(title))

        # Convert spaces to underscores.
        title = title.replace("_", " ")
        # Replace strings of underscores with a single underscore.
        title = MULTIPLE_SPACES.sub(" ", title)
        # Remove all underscores from the start and end.
        title = title.strip()

        # The parts are separate by colons.
        parts = title.split(":")
        has_interwiki = title and title[0] == ":"

        # Generally only 1 - 3 parts are expected (interwiki, namespace, and title).
        num_parts = len(parts)
        if num_parts >= 4:
            if has_interwiki:
                interwiki = parts[1]
                parts = parts[2:]
            else:
                interwiki = ""
            namespace = parts[0]
            title = ":".join(parts[1:])
        elif num_parts == 3:
            if has_interwiki:
                _, interwiki, title = parts
                namespace = default_namespace
            else:
                interwiki = ""
                namespace = parts[0]
                title = ":".join(parts[1:])
        elif num_parts == 2:
            # In this case an interwiki link cannot be given.
            interwiki = ""
            namespace, title = parts
        else:
            # No colons, it is just a page title.
            interwiki = ""
            namespace = default_namespace
            title = parts[0]

        # Each of the pieces again has and starting / trailing underscores removed.
        interwiki = interwiki.strip()
        namespace = namespace.strip()
        title = title.strip()

        # According to the MediaWiki docs, the namespace gets canonicalized to
        # upper-case, then all lower-case. This doesn't seem accurate (see how
        # it treats the "MediaWiki" namespace).
        try:
            canonical_namespace = self._canonical_namespaces[
                _normalize_namespace(namespace)
            ]
        except KeyError:
            canonical_namespace = namespace

        return CanonicalTitle(canonical_namespace, _normalize_title(title), interwiki)

    def get_magic_word(self, magic_word: str) -> MagicWord:
        """Given a magic word, return the callable for it."""
        try:
            return self._magic_words[magic_word]
        except KeyError:
            raise MagicWordNotFound(magic_word)

    def add_magic_word(self, magic_word: str, function: MagicWord) -> None:
        """Add an additional magic word."""
        self._magic_words[magic_word] = function

    def get_parser_function(self, parser_function: str) -> ParserFunction:
        try:
            return self._parser_functions[parser_function]
        except KeyError:
            raise ParserFunctionNotFound(parser_function)

    def add_parser_function(
        self, parser_function: str, function: ParserFunction
    ) -> None:
        """Add an additional magic word."""
        self._parser_functions[parser_function] = function
