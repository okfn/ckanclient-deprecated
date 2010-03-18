try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from ckanclient import __version__, __description__, __long_description__, __license__

import os
scripts = [
    os.path.join('bin', 'ckanload-aidprojdata'),
    os.path.join('bin', 'ckanload-norwaygovdata'),
]

setup(
    name='ckanclient',
    version=__version__,
    author='Appropriate Software Foundation, Open Knowledge Foundation',
    author_email='info@okfn.org',
    license=__license__,
    url='http://www.okfn.org/ckan/',
    description=__description__,
    keywords='data packaging component tool client',
    long_description =__long_description__,
    install_requires=[
        # only required if python <= 2.5 (as json library in python >= 2.6)
        # 'simplejson',
    ],
    packages=find_packages(exclude=['ez_setup']),
    scripts=scripts,
    include_package_data=True,
    always_unzip=True,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'],
)
