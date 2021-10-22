import argparse
import sys

import mwparserfromhell

import mwcomposerfromhell


def convert_file(filename: str, wrap: bool) -> None:
    with open(filename) as f:
        text = f.read()

    wikicode = mwparserfromhell.parse(text)

    if wrap:
        print("<html>\n<head></head>\n<body>\n")
    print(mwcomposerfromhell.compose(wikicode))
    if wrap:
        print("</body>\n</html>\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert wikicode to HTML.")
    parser.add_argument(
        "-w",
        "--wrap",
        action="store_true",
        help="Wrap the output in <html> and <body> tags.",
    )
    parser.add_argument("file", help="The file containing wikicode to convert.")

    # Parse the command line arguments.
    args = parser.parse_args(sys.argv[1:])

    convert_file(args.file, args.wrap)
