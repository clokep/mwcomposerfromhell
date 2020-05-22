import mwparserfromhell
import pytest

from mwcomposerfromhell.namespace import ArticleNotFound, ArticleResolver, Namespace


@pytest.fixture
def resolver():
    """Create an ArticleResolver with some pre-filled articles."""
    # Main articles.
    main = {
        'Foo': 'Foo!',  # Overlaps with a template.
        'Main': 'Blah',
    }

    # Some templates.
    templates = {
        'Echo': '{{{1}}}',
        'Foo': 'This is a template',
    }

    # Create the resolver and add the namespaces to it.
    resolver = ArticleResolver()

    for name, articles in (('', main), ('Template', templates)):
        articles = {
            name: mwparserfromhell.parse(article) for name, article in articles.items()
        }
        resolver.add_namespace(name, Namespace(articles))

    return resolver


def test_namespace_not_found(resolver):
    """Try to get an article from a non-existent namespace."""
    with pytest.raises(ArticleNotFound):
        resolver.get_article('Fuzz:Bar')


def test_article_not_found(resolver):
    """Try to get an article from an existent namespace that doesn't exist."""
    # Without a namespace.
    with pytest.raises(ArticleNotFound):
        resolver.get_article('Blah')
    # With a namespace
    with pytest.raises(ArticleNotFound):
        resolver.get_article('Template:Blah')


def test_get_article(resolver):
    """Test getting an article."""
    assert resolver.get_article('Main')
    assert resolver.get_article('Template:Echo')


def test_shadowed(resolver):
    """The namespace should be honored when getting an article."""
    assert resolver.get_article('Foo') != resolver.get_article('Template:Foo')


def test_case_insensitivity(resolver):
    """The first letter is case-insensitive."""
    assert resolver.get_article('Main') == resolver.get_article('main')

    # The case of other letters matters.
    with pytest.raises(ArticleNotFound):
        resolver.get_article('MAIN')

    # The same applies to namespaces.
    foo = resolver.get_article('Template:Foo')
    assert foo == resolver.get_article('Template:Foo')
    assert foo == resolver.get_article('template:Foo')
    assert foo == resolver.get_article('template:foo')

    with pytest.raises(ArticleNotFound):
        resolver.get_article('TEMPLATE:Foo')
    with pytest.raises(ArticleNotFound):
        resolver.get_article('Template:FOO')
