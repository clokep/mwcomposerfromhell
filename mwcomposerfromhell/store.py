import json
import re

import mwparserfromhell


class CachingStore:
    """A store which caches to disk."""
    def __init__(self, file_path, *args, **kwargs):
        super(DownloadingStore, self).__init__(*args, **kwargs)

        # Load previously created values from disk.
        with open(file_path, 'r') as f:
            self._cache = json.load(f)

    def __setitem__(self, key, value):
        # Set the item, like normal.
        result = super(FoobarCache, self).__setitem__(key, value)

        # Cache to disk.
        with open(file_path, 'w') as f:
            json.dump(self._cache, f)

        return result


def get_article(url):
    """Fetches and returns the article content as a string."""
    response = requests.get(url, params={'action': 'raw'})
    return response.text


class DownloadingStore:
    """A store which automatically downloads templates on first use."""
    NOINCLUDE_PATTERN = re.compile(r'<noinclude>.*?</noinclude>', flags=re.DOTALL)
    INCLUDEONLY_PATTERN = re.compile(r'<includeonly>(.*?)</includeonly>', flags=re.DOTALL)

    def __init__(self, base_url, *args, **kwargs):
        super(DownloadingStore, self).__init__(*args, **kwargs)
        self._base_url = base_url

    def __getitem__(self, key):
        try:
            template = self._cache[key]
        except KeyError:
            # Get the template from the server.
            article_url = get_article_url(self._base_url, 'Template:' + key)
            template_str = get_article(article_url)

            # Only use the parts that would be included.
            template_str = self.NOINCLUDE_PATTERN.sub(r'', template_str)
            template_str = self.INCLUDEONLY_PATTERN.sub(r'\1', template_str)

            # Parse the template to Wikicode
            template = mwparserfromhell.parse(template_str)

            # Store it for subsequent calls.
            self[key] = template

        return template

    def __setitem__(self, key, value):
        self._cache[key] = value
        return value


class DownloadingCache(DownloadingStore, CachingStore):
    pass
