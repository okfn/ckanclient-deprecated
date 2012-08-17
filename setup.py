try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from ckanclient import __version__, __description__, __long_description__, __license__

import os

install_requires = []
try:
    __import__('json')
except ImportError:
    # The json module isn't available in the standard library until 2.6;
    # use simplejson instead,
    install_requires.append('simplejson')

setup(
    name='ckanclient',
    version=__version__,
    author='Open Knowledge Foundation',
    author_email='info@okfn.org',
    license=__license__,
    url='https://github.com/okfn/ckanclient',
    description=__description__,
    keywords='data packaging component tool client',
    long_description =__long_description__,
    install_requires=install_requires,
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    always_unzip=True,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    test_suite = 'nose.collector',
)
