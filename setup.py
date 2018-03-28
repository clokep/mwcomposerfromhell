import codecs

from setuptools import setup, find_packages

def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()


setup(
    name='mwcomposerfromhell',
    version="0.1",
    packages=find_packages(),
    description='',
    long_description=long_description(),
    author='Patrick Cloke',
    author_email='clokep@patrick.cloke.us',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: ISC License (ISCL)',
    ],
)
