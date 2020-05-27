from collections import namedtuple
import html
import re
from typing import Any, Dict, Tuple
from urllib.parse import unquote


MULTIPLE_UNDERSCORES = re.compile(r'_+')


class ArticleNotFound(Exception):
    """The article was not found."""


CanonicalTitle = namedtuple('CanonicalTitle', ('namespace', 'title', 'interwiki'))


def _normalize_spaces(key: str) -> str:
    """Spaces and turned to underscores, multiple get combined, and stripped from the beginning and end."""
    # Convert spaces to underscores.
    key = key.replace(' ', '_')
    # Replace strings of underscores with a single underscore.
    key = MULTIPLE_UNDERSCORES.sub('_', key)
    # Remove all underscores from the start and end.
    return key.strip('_')


def _normalize_namespace(key: str) -> str:
    """MediaWiki treats the first character of namespaces as upper-case and the rest as lower-case."""
    if not key:
        return ''
    key = _normalize_spaces(key)
    return key[0].upper() + key[1:].lower()


def _normalize_title(key: str) -> str:
    """MediaWiki treats the first character of article names as upper-case."""
    if not key:  # Empty string
        return ''
    key = _normalize_spaces(key)
    return key[0].upper() + key[1:]


def canonicalize_title(title: str) -> str:
    """
    Generate the canonical form of a title.

    See https://en.wikipedia.org/wiki/Help:Link#Conversion_to_canonical_form

    TODO Handle anonymous user pages.
    """
    # HTML entities and percent encoded characters get converted to their raw
    # character.
    title = html.unescape(unquote(title))

    # Convert spaces to underscores.
    title = title.replace(' ', '_')
    # Replace strings of underscores with a single underscore.
    title = MULTIPLE_UNDERSCORES.sub('_', title)
    # Remove all underscores from the start and end.
    title = title.strip('_')

    # The parts are separate by colons.
    parts = title.split(':')
    has_interwiki = title[0] == ':'

    # Generally only 1 - 3 parts are expected (interwiki, namespace, and title).
    num_parts = len(parts)
    if num_parts >= 4:
        if has_interwiki:
            interwiki = parts[1]
            parts = parts[2:]
        else:
            interwiki = ''
        namespace = parts[0]
        title = ':'.join(parts[1:])
    elif num_parts == 3:
        if has_interwiki:
            _, interwiki, title = parts
            namespace = ''
        else:
            interwiki = ''
            namespace = parts[0]
            title = ':'.join(parts[1:])
    elif num_parts == 2:
        # In this case an interwiki link cannot be given.
        interwiki = ''
        namespace, title = parts
    else:
        # No colons, it is just a page title.
        interwiki = ''
        namespace = ''
        title = parts[0]

    # Each of the pieces again has and starting / trailing underscores removed.
    interwiki = interwiki.strip('_')
    namespace = namespace.strip('_')
    title = title.strip('_')

    return CanonicalTitle(_normalize_namespace(namespace), _normalize_title(title), interwiki)


class Namespace:
    """
    A Namespace maps article names (as strings) to
    ``mwparserfromhell.wikicode.Wikicode`` instances.

    Note that each article is expected to already have the namespace name removed.
    """

    def __init__(self, articles: Dict[str, Any] = None):
        if articles is None:
            self._articles = {}
        else:
            # Fix the names of any incoming articles.
            self._articles = {
                _normalize_title(name): article for name, article in articles.items()
            }

    def __getitem__(self, key: str) -> Any:
        return self._articles[_normalize_title(key)]

    def __setitem__(self, key: str, value: Any) -> Any:
        self._articles[_normalize_title(key)] = value
        return value


class ArticleResolver:
    def __init__(self):
        self._namespaces = {}  # Dict[str, Namespace]

    def add_namespace(self, name: str, namespace: Namespace) -> None:
        self._namespaces[_normalize_namespace(name)] = namespace

    def resolve_article(self, name: str, default_namespace: str) -> Tuple[str, str]:
        """
        Get the canonical namespace and name for an article.

        :param name: The name of the article to find.
        :param default_namespace: The namespace to use, if one is not provided.
        """
        canonical_title = canonicalize_title(name)
        # Use the default namespace if one was not parsed.
        if not canonical_title.namespace and default_namespace:
            return CanonicalTitle(default_namespace, *canonical_title[1:])
        return canonical_title

    def get_article(self, name: str, default_namespace: str = ''):
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
