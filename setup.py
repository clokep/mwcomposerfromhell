import codecs

from setuptools import find_packages, setup


def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()


setup(
    name='mwcomposerfromhell',
    version='0.5dev',
    packages=find_packages(exclude=('tests', )),
    description='Convert the parsed MediaWiki wikicode (using mwparserfromhell) to HTML.',
    long_description=long_description(),
    author='Patrick Cloke',
    author_email='clokep@patrick.cloke.us',
    url='https://github.com/clokep/mwcomposerfromhell',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: ISC License (ISCL)',
    ],
    install_requires=[
        'mwparserfromhell>=0.5',
    ],
    extras_require={
        "dev": [
            # For running tests.
            "pytest==5.4.2",
            'coverage',
            # Style checking.
            "flake8==3.8.2",
            "flake8-builtins==1.5.3",  # For disallowing shadowing of Python built-ins.
            "flake8-import-order==0.18.1",
            # Typing related.
            "mypy",
        ],
    },
)
