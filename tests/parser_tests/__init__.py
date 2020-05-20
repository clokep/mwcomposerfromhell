# All potential sections:
# article
# config
# end
# endarticle
# html
# html+tidy
# html/*
# html/parsoid
# html/php
# html/php+disabled
# html/php+tidy
# html/php+tidy-DISABLED
# options
# test
# text
# wikitext
# wikitext/edited
import re

# This wants to match things that are:
# * An character string.
# * An character string with a value of characters, commas, etc.
# * "title=" with the title enclosed in [[ ]].
OPTION_PATTERN = re.compile(r'([a-z]+)(?:=([a-zA-Z0-9,\-]+)|=\[\[([a-zA-Z ]+)\]\])?')


class MediaWikiParserTestCasesParser:
    def __init__(self, file):
        self._file = file
        self.articles = {}
        self.test_cases = []

    def visit(self, section, contents):
        method_name = 'visit_' + section

        try:
            method = getattr(self, method_name)
        except AttributeError:
            raise RuntimeError('Unknown section type: {}'.format(section))

        method(contents)

    def visit_article(self, contents):
        """
        An article must have the following fields:

        * article: The name of the article (including the namespace, e.g. "Foo"
          or "Template:Bar").
        * contents: The contents of the article.

        """
        # Ensure articles don't have other info we're missing.
        unknown_params = set(contents.keys()) - {"article", "text"}
        if unknown_params:
            raise ValueError(
                "Unknown parameters: %s" % ' '.join(sorted(unknown_params)))

        # Articles should be unique.
        article_name = contents["article"].strip()
        if article_name in self.articles:
            raise ValueError("Cannot overwrite an article: %s" % article_name)

        self.articles[article_name] = contents["text"]

    def visit_test(self, contents):
        """
        A test must have the following fields:

        * wikitext: The contents of the test.

        It can also have a bunch of option fields, but likely has at least one
        starting with "html" to show the output.
        """
        # Options are separated by whitespace, kind of. Some also have values.
        options_str = contents.get('options')
        options = {}
        if options_str:
            matches = OPTION_PATTERN.findall(options_str)
            # Map each option to a value of one of the matches or True.
            for m in matches:
                options[m[0]] = m[1] or m[2] or True
        contents['options'] = options

        self.test_cases.append(contents)

    def parse(self):
        current_group = None
        current_parameter = None
        contents = ''
        group_end = None
        parameters = {}

        # Somewhat like TestFileReader.execute().
        for line in self._file.readlines():
            # A new section was found.
            if line.startswith('!!'):
                # The type of section found.
                current_section = line[2:].strip().lower()

                # If not already in a group, this is the start of a new group.
                if not current_group:
                    if current_section not in ('article', 'test'):
                        raise ValueError("Unexpected section: '{}'".format(current_section))

                    current_group = current_section
                    current_parameter = current_section

                    # Calculate the section type which ends this grouping.
                    if current_section == 'article':
                        group_end = 'endarticle'
                    else:
                        group_end = 'end'

                # If already in a group, this starts a new parameter.
                else:
                    parameters[current_parameter] = contents

                    if current_section == group_end:
                        self.visit(current_group, parameters)
                        current_group = None
                        current_parameter = None
                        contents = ''
                        group_end = None
                        parameters = {}

                    else:
                        # Reset.
                        current_parameter = current_section
                        contents = ''

            # If in a group, concatent lines in each section.
            elif current_group:
                contents += line

            # Otherwise do nothing to ignore any content outside of a section.
