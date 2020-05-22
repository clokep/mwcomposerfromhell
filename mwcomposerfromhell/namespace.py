from typing import Any, Dict, Tuple


class ArticleNotFound(Exception):
    """The article was not found."""


def _clean_name(key: str) -> str:
    """MediaWiki treats the first character of article names as case-insensitive."""
    if not key:  # Empty string
        return key
    return key[0].lower() + key[1:]


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
                _clean_name(name): article for name, article in articles.items()
            }

    def __getitem__(self, key: str) -> Any:
        return self._articles[_clean_name(key)]

    def __setitem__(self, key: str, value: Any) -> Any:
        self._articles[_clean_name(key)] = value
        return value


class ArticleResolver:
    def __init__(self):
        self._namespaces = {}  # Dict[str, Namespace]

    def add_namespace(self, name: str, namespace: Namespace) -> None:
        self._namespaces[_clean_name(name)] = namespace

    def resolve_article(self, name: str, default_namespace: str) -> Tuple[str, str]:
        """
        Get the canonical namespace and name for an article.

        :param name: The name of the article to find.
        :param default_namespace: The namespace to use, if one is not provided.
        """
        parts = name.split(':', 1)
        # If there was not a colon, it is in the main namespace, which is a
        # blank string.
        if len(parts) == 1:
            return default_namespace, parts[0]
        return tuple(parts)  # type: ignore

    def get_article(self, name: str, default_namespace: str = ''):
        """
        Get an article's content (as ``mwparserfromhell.wikicode.Wikicode``) from a name.

        :param name: The name of the article to find.
        :param default_namespace: The namespace to use, if one is not provided.
        """
        namespace, name = self.resolve_article(name, default_namespace)

        try:
            return self._namespaces[_clean_name(namespace)][name]
        except KeyError:
            raise ArticleNotFound(namespace, name)
