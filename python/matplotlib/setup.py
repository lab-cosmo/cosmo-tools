import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "cosmoplot",
    version = "0.0.1",
    author = "Benjamin Helfrecht",
    author_email = "benjamin.helfrecht@epfl.ch",
    description = ("Common utils for cosmo publications"),
    license = "Unknown",
    url = "https://github.com/cosmo-epfl/cosmo-tools",
    packages=['cosmoplot'],
    long_description=read('README.md'),
)
