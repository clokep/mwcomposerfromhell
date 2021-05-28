import pytest

from mwcomposerfromhell import magic_words


def patch_datetime(expected_datetime):
    @pytest.fixture(autouse=True)
    def patch(monkeypatch):
        """Give a stable date for the tests."""

        class MockDatetime:
            @classmethod
            def now(cls):
                return expected_datetime

            @classmethod
            def utcnow(cls):
                return expected_datetime

        monkeypatch.setattr(magic_words, "datetime", MockDatetime)

    return patch
