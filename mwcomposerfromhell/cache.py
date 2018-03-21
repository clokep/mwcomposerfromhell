import re

import mwparserfromhell


class DownloadingCache:
    NOINCLUDE_PATTERN = re.compile(r'<noinclude>.*?</noinclude>', flags=re.DOTALL)
    INCLUDEONLY_PATTERN = re.compile(r'<includeonly>(.*?)</includeonly>', flags=re.DOTALL)

    def __getitem__(self, key):
        try:
            template = self._cache[key]
        except KeyError:
            # Get the template from the server.
            template_str = get_article(get_article_url('Template:' + key))

            # Only use the parts that would be included.
            template_str = self.NOINCLUDE_PATTERN.sub(r'', template_str)
            template_str = self.INCLUDEONLY_PATTERN.sub(r'\1', template_str)

            # Parse the template to Wikicode
            template = mwparserfromhell.parse(template_str)

            # Store it for subsequent calls.
            self._cache[key] = template

        return template
