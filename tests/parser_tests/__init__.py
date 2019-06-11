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


class MediaWikiParserTestCasesParser:
    def __init__(self, file):
        self._file = file
        self.articles = []
        self.test_cases = []

    def visit(self, section, contents):
        method_name = 'visit_' + section

        try:
            method = getattr(self, method_name)
        except AttributeError:
            raise RuntimeError('Unknown section type: {}'.format(section))

        method(contents)

    def visit_article(self, contents):
        self.articles.append(contents)

    def visit_test(self, contents):
        self.test_cases.append(contents)

    def parse(self):
        current_section = None
        current_parameter = None
        contents = ''
        end_section = None
        parameters = {}

        # Somewhat like TestFileReader.execute().
        for line in self._file.readlines():
            # A new section was found.
            if line.startswith('!!'):
                section = line[2:].strip().lower()

                if not current_section:
                    if section not in ('article', 'test'):
                        raise ValueError("Unexpected section: '{}'".format(section))

                    current_section = section
                    current_parameter = section

                    end_section = 'end'
                    if section == 'article':
                        end_section = 'endarticle'

                else:
                    parameters[current_parameter] = contents

                    if section == end_section:
                        self.visit(current_section, parameters)
                        current_section = None
                        current_parameter = None
                        contents = ''
                        end_section = None
                        parameters = {}

                    else:
                        # Reset.
                        current_parameter = section
                        contents = ''

            # Ignore any content outside of a section.
            elif current_section:
                contents += line
