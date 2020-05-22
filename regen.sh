# Regenerate the whitelist of passing tests by running all tests and seeing what passes.
pytest tests/parser_tests/test_mediawiki.py -v | grep "PASSED" | cut -d '[' -f 2 | cut -d ']' -f 1 > tests/parser_tests/whitelist.txt
