ckanclient makes is a Python module to read and write to a CKAN server 
via the API.

Usage
=====

To see how to use the ckanclient, see the docs in __init__.py


Retrieval
=========

You can download releases of ckanclient from PyPI::

    <http://pypi.python.org/pypi/ckanclient>

or you can get the latest repository using Mercurial::

    hg clone https://knowledgeforge.net/ckan/ckanclient


Tests
=====

The ckanclient tests require a test instance of CKAN running at 
127.0.0.1:5000 (for more info, see <http://knowledgeforge.net/ckan/>)::

    paster db clean && paster db init && paster create-test-data
    paster serve development.ini

In another shell, ensure 'nose' is installed::

    easy_install nose

Now run the ckanclient tests::

    nosetests ckanclient/tests
