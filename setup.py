import codecs

from setuptools import find_packages, setup


def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()


setup(
    name='mwcomposerfromhell',
    version="0.2dev",
    packages=find_packages(),
    description='Convert the parsed MediaWiki wikicode (using mwparserfromhell) to HTML.',
    long_description=long_description(),
    author='Patrick Cloke',
    author_email='clokep@patrick.cloke.us',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: ISC License (ISCL)',
    ],
    install_requires=[
        'mwparserfromhell>=0.5',
    ],
)
