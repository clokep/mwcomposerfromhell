import json
import re
from typing import Any, TextIO

# The types of the option dict.
JSON_VALUE = dict[str, Any]
OPTION_VALUE = bool | list[str] | list[JSON_VALUE]

# Patterns for parsing options.
UNQUOTED_PATTERN = re.compile(r"\s*([\w-]+)\s*")
QUOTED_PATTERN = re.compile(r'\s*"([^"]*)"\s*')
# The pattern for a link is hard to read, but it is essentially [[, followed by
# content, followed by ]].
LINK_PATTERN = re.compile(r"\s*\[\[([^\]]*)\]\]\s*")


def _parse_options(options_str: str) -> dict[str, OPTION_VALUE]:
    """
    Options take one of the following forms:

    * abc
    * abc=def
    * abc="def ghi"
    * abc=[[def ghi]]
    * abc=def,"ghi jkl"
    * abc=JSON object

    This returns a dictionary which maps the option keys to a value. The value
    is either a boolean (if there was no value), a list of strings, or a JSON
    object.
    """
    result: dict[str, OPTION_VALUE] = {}
    pos = 0
    options_len = len(options_str)

    # Start at the beginning.
    while pos < options_len:
        # Find the first key.
        match = UNQUOTED_PATTERN.search(options_str, pos)

        if not match:
            break

        # Pull out the new key and move the cursor.
        key = match[1]
        pos = match.end(0)

        # If there's no value, we're done.
        if pos == options_len or options_str[pos] != "=":
            result[key] = True
            continue

        # Skip the equals sign and parse the value.
        pos += 1

        # The value can be a normal value, a quoted string, a link title, or JSON.
        values = []

        while True:
            # Ensure not at end of string.
            if pos == options_len:
                # This shouldn't happen.
                raise ValueError("Unexpected end of string: no value provided.")

            # The start of a string, find the corresponding quote.
            elif options_str[pos] == '"':
                # Find the next quote.
                match = QUOTED_PATTERN.search(options_str, pos)
                if not match:
                    raise ValueError("Unmatched quote.")
                values.append(match[1])
                pos = match.end(0)

            # The start of a link title, find the corresponding close.
            elif options_str[pos] == "[":
                match = LINK_PATTERN.search(options_str, pos)
                if not match:
                    raise ValueError("Unmatched link.")
                values.append(match[1])
                pos = match.end(0)

            # The start of a JSON object.
            elif options_str[pos] == "{":
                # Iterate through the string until an equal number of open and
                # close braces are found outside of strings.
                #
                # This is kind of terrible, but we don't know where the end of
                # the JSON object is, so we greedily parse.
                count = 0
                in_str = False
                temp_pos = pos
                while temp_pos < options_len:
                    c = options_str[temp_pos]
                    if not in_str:
                        if c == "{":
                            count += 1
                        elif c == "}":
                            count -= 1
                    if c == '"':
                        # If the previous character was a backslash, ignore it.
                        if options_str[temp_pos - 1] != "\\":
                            in_str = not in_str
                    if not count:
                        break
                    temp_pos += 1
                else:
                    raise ValueError("Unbalanced braces.")

                # Load the JSON data.
                json_data = options_str[pos : temp_pos + 1]
                values.append(json.loads(json_data))

                pos = temp_pos + 1

            # Otherwise, just a normal string.
            else:
                match = UNQUOTED_PATTERN.search(options_str, pos)
                if not match:
                    raise ValueError("Expected a value.")
                values.append(match[1])
                pos = match.end(0)

            # If there are more values, continue parsing them.
            if pos == options_len or options_str[pos] != ",":
                break

        result[key] = values

    return result


class MediaWikiParserTestsParser:
    """
    Read and parse MediaWiki test case files.

    Each file can include articles, templates, etc. as well as test cases.

    After running ``parse()``, access the ``articles`` and ``test_cases`` properties.

    """

    def __init__(self, file: TextIO):
        self._file = file
        self.articles: dict[str, str] = {}
        self.test_cases: list[dict[str, Any]] = []
        # Track if we've seen options in the current test.
        self._test_has_options: bool = False

    def visit(self, section: str, contents: dict[str, str]) -> None:
        method_name = "visit_" + section

        try:
            method = getattr(self, method_name)
        except AttributeError:
            raise RuntimeError(f"Unknown section type: {section}") from None

        method(contents)

    def visit_article(self, contents: dict[str, str]) -> None:
        """
        An article must have the following fields:

        * article: The name of the article (including the namespace, e.g. "Foo"
          or "Template:Bar").
        * contents: The contents of the article.

        """
        # Ensure articles don't have other info we're missing.
        unknown_params = set(contents.keys()) - {"article", "text"}
        if unknown_params:
            raise ValueError("Unknown parameters: " + " ".join(sorted(unknown_params)))

        # Articles should be unique.
        article_name = contents["article"].strip()
        if article_name in self.articles:
            raise ValueError(f"Cannot overwrite an article: {article_name}")

        self.articles[article_name] = contents["text"]

    def visit_test(self, contents: dict[str, Any]) -> None:
        """
        A test must have the following fields:

        * wikitext: The contents of the test.

        It can also have a bunch of option fields, but likely has at least one
        starting with "html" to show the output.
        """
        # Options take one of the following forms:
        #
        # * abc
        # * abc=def
        # * abc="def ghi"
        # * abc=[[def ghi]]
        # * abc=def,"ghi jkl"
        # * abc=JSON object

        # Options are separated by whitespace, kind of. Some also have values.
        # Config is already merged into options by the parse() method.
        options = contents.get("options")
        if isinstance(options, str):
            options = _parse_options(options)

        contents["options"] = options if options is not None else {}

        self.test_cases.append(contents)

    def parse(self) -> None:
        current_group: str | None = None
        current_parameter: str | None = None
        contents = ""
        group_end: str | None = None
        parameters: dict[str, Any] = {}

        # Somewhat like TestFileReader.execute().
        for line in self._file.readlines():
            # A new section was found.
            if line.startswith("!!"):
                # The type of section found.
                current_section = line[2:].strip().lower()

                # If not already in a group, this is the start of a new group.
                if not current_group:
                    if current_section not in ("article", "test", "version 2"):
                        raise ValueError(f"Unexpected section: '{current_section}'")

                    # "version 2" is a marker section that doesn't start a new group.
                    if current_section == "version 2":
                        current_group = None
                    else:
                        current_group = current_section
                        current_parameter = current_section

                        # Calculate the section type which ends this grouping.
                        if current_section == "article":
                            group_end = "endarticle"
                        else:
                            group_end = "end"

                # If already in a group, this starts a new parameter.
                else:
                    # Flush accumulated contents to the current parameter.
                    if current_parameter is not None:
                        existing = parameters.get(current_parameter, "")
                        if isinstance(existing, str):
                            parameters[current_parameter] = existing + contents
                        # If it's a dict (parsed options), don't append string content.

                    if current_section == group_end:
                        # We've completed the group, visit it.
                        self.visit(current_group, parameters)
                        current_group = None
                        current_parameter = None
                        contents = ""
                        group_end = None
                        parameters = {}

                    elif current_section == "options":
                        # "!! options" - test name is complete, options start fresh.
                        current_parameter = "options"
                        parameters["options"] = ""
                        contents = ""

                    elif current_section == "config":
                        # "!! config" - if options is a string, parse it; otherwise
                        # accumulate config content.
                        options = parameters.get("options")
                        if options is not None and isinstance(options, str):
                            # Parse the accumulated options content.
                            if options.strip():
                                parameters["options"] = _parse_options(options.strip())
                        # Start accumulating config content.
                        parameters["config"] = ""
                        current_parameter = "config"
                        contents = ""

                    elif current_section in ("wikitext", "html"):
                        # "!! wikitext" or "!! html" - merge config into options, start accumulating.
                        options = parameters.get("options")
                        config = parameters.get("config", "")

                        # Ensure options is a dict.
                        if options is None:
                            options_dict: dict[str, OPTION_VALUE] = {}
                        elif isinstance(options, str):
                            options_dict = (
                                _parse_options(options.strip())
                                if options.strip()
                                else {}
                            )
                        else:
                            options_dict = options

                        # Merge config content into options.
                        if config and isinstance(config, str):
                            for config_line in config.strip().split("\n"):
                                config_line = config_line.strip()
                                if not config_line or config_line.startswith("!!"):
                                    break
                                try:
                                    params = _parse_options(config_line)
                                    options_dict.update(params)
                                except ValueError:
                                    # Skip invalid config lines.
                                    pass

                        parameters["options"] = options_dict
                        current_parameter = current_section
                        parameters[current_section] = ""
                        contents = ""

                    else:
                        # Unknown section - reset.
                        current_parameter = current_section
                        parameters[current_section] = ""
                        contents = ""

            # If in a group, concatent lines in each section.
            elif current_group:
                contents += line

            # Otherwise do nothing to ignore any content outside of a section.
