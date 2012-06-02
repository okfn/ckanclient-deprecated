ckanclient is a Python module to read and write to a CKAN server
via the API.

Usage
=====

To see how to use the ckanclient, see the docs in `__init__.py`


Retrieval
=========

You can download releases of ckanclient from PyPI:

http://pypi.python.org/pypi/ckanclient

or you can get the latest repository using Mercurial::

    git clone https://github.com/okfn/ckanclient.git


Tests
=====

The ckanclient tests require the ckan and nose modules installed. Optionally 
ckanext-dgu can be installed too and the form api will be tested.

To run the tests::

    nosetests --ckan ckanclient/tests
