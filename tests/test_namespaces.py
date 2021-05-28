import mwparserfromhell
import pytest

from mwcomposerfromhell.namespace import (
    ArticleNotFound,
    ArticleResolver,
    Namespace,
)


@pytest.fixture
def resolver():
    """Create an ArticleResolver with some pre-filled articles."""
    # Main articles.
    main = {
        "Foo": "Foo!",  # Overlaps with a template.
        "Main": "Blah",
    }

    # Some templates.
    templates = {
        "Echo": "{{{1}}}",
        "Foo": "This is a template",
    }

    # Create the resolver and add the namespaces to it.
    resolver = ArticleResolver()

    for name, articles in (("", main), ("Template", templates), ("MediaWiki", {})):
        articles = {
            name: mwparserfromhell.parse(article) for name, article in articles.items()
        }
        resolver.add_namespace(name, Namespace(articles))

    return resolver


def test_namespace_not_found(resolver):
    """Try to get an article from a non-existent namespace."""
    with pytest.raises(ArticleNotFound):
        resolver.get_article("Fuzz:Bar")


def test_article_not_found(resolver):
    """Try to get an article from an existent namespace that doesn't exist."""
    # Without a namespace.
    with pytest.raises(ArticleNotFound):
        resolver.get_article("Blah")
    # With a namespace
    with pytest.raises(ArticleNotFound):
        resolver.get_article("Template:Blah")


def test_get_article(resolver):
    """Test getting an article."""
    assert resolver.get_article("Main")
    assert resolver.get_article("Template:Echo")


def test_shadowed(resolver):
    """The namespace should be honored when getting an article."""
    assert resolver.get_article("Foo") != resolver.get_article("Template:Foo")


def test_case_sensitivity(resolver):
    """The first letter is automatically capitalized."""
    assert resolver.get_article("Main") == resolver.get_article("main")

    # The case of other letters matters.
    with pytest.raises(ArticleNotFound):
        resolver.get_article("MAIN")

    # The case of namespaces is normalized.
    foo = resolver.get_article("Template:Foo")
    assert foo == resolver.get_article("Template:Foo")
    assert foo == resolver.get_article("template:Foo")
    assert foo == resolver.get_article("template:foo")
    assert foo == resolver.get_article("TEMPLATE:Foo")

    with pytest.raises(ArticleNotFound):
        resolver.get_article("Template:FOO")


@pytest.mark.parametrize(
    ("target",),
    [
        # Standard form.
        ("Main page",),
        # First character gets upper-cased.
        ("main page",),
        # Underscores.
        ("Main_page",),
        # Extra underscores.
        ("__Main_page___",),
        # Extra spaces.
        ("  Main page   ",),
        # Namespace.
        (":main page",),
    ],
)
def test_canonicalize(target, resolver):
    """Test canonicalizing an article in the main namespace."""
    assert resolver.canonicalize_title(target) == ("", "Main page", "")


@pytest.mark.parametrize(
    ("target",),
    [
        # Standard form.
        ("Template:Foo bar",),
        # First character gets upper-cased.
        ("template:foo bar",),
        # Underscores.
        ("template:foo_bar",),
        # Extra underscores.
        ("__template__:__foo_bar___",),
        # Extra spaces.
        ("  template   :  foo bar   ",),
    ],
)
def test_canonicalize_with_namespace(target, resolver):
    """Test canonicalizing an article in the template namespace."""
    assert resolver.canonicalize_title(target) == ("Template", "Foo bar", "")


def test_canonicalize_with_odd_namespace(resolver):
    """Test canonicalizing an article in the main namespace."""
    assert resolver.canonicalize_title("MediaWiki:Foo") == ("MediaWiki", "Foo", "")
    # An unknown namespace passes through without being modified.
    assert resolver.canonicalize_title("UNknown:Foo") == ("UNknown", "Foo", "")


@pytest.mark.parametrize(
    ("target",),
    [
        # Standard form.
        (":en:Foo bar",),
        # Underscores.
        (":en:foo_bar",),
        # Extra underscores.
        ("__:__en__:__foo_bar___",),
        # Extra spaces.
        ("  :  en   :  foo bar   ",),
    ],
)
def test_canonicalize_with_interwiki(target, resolver):
    """Test canonicalizing an interwiki article in the main namespace."""
    assert resolver.canonicalize_title(target) == ("", "Foo bar", "en")


@pytest.mark.parametrize(
    ("target",),
    [
        # Standard form.
        (":en:Template:Foo bar",),
        # Underscores.
        (":en:Template:foo_bar",),
        # Extra underscores.
        ("__:__en__:__Template__:__foo_bar___",),
        # Extra spaces.
        ("  :  en   :  Template  :  foo bar   ",),
    ],
)
def test_canonicalize_with_namespace_and_interwiki(target, resolver):
    """Test canonicalizing an interwiki article in the template namespace"""
    assert resolver.canonicalize_title(target) == ("Template", "Foo bar", "en")


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        # HTML entities.
        ("d&eacute;partement", "Département"),
        # Percent-encoded.
        ("%40", "@"),
        # Percent and HTML encoded! (%26 = &)
        ("Foo%26amp;", "Foo&"),
        # Encoded colons get unescaped first.
        ("%3Ade%3AFoo", ("", "Foo", "de")),
    ],
)
def test_canonicalize_escape(target, expected, resolver):
    """Test canonicalizing an article with oddly encoded characters."""
    if isinstance(expected, str):
        expected = ("", expected, "")
    assert resolver.canonicalize_title(target) == expected


@pytest.mark.parametrize(
    ("target", "expected_interwiki"),
    [
        # Standard form.
        (
            "Main page",
            "",
        ),
        # First character gets upper-cased.
        (
            "main page",
            "",
        ),
        # Underscores.
        (
            "Main_page",
            "",
        ),
        # Extra underscores.
        (
            "__Main_page___",
            "",
        ),
        # Extra spaces.
        (
            "  Main page   ",
            "",
        ),
        # Only an interwiki.
        (
            ":en:Main page",
            "en",
        ),
    ],
)
def test_canonicalize_with_default_namespace(target, expected_interwiki, resolver):
    """Test canonicalizing an article with a default namespace."""
    assert resolver.canonicalize_title(target, "Default") == (
        "Default",
        "Main page",
        expected_interwiki,
    )
