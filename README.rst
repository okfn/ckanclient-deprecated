ckanclient is a Python library and command-line client to read and write to a
CKAN instance via the API. It covers both the Catalog and `Data API`_
(accessing the `CKAN DataStore`_).

.. _Data API: http://docs.ckan.org/en/latest/using-data-api.html
.. _CKAN DataStore: http://docs.ckan.org/en/latest/datastore.html

Usage
=====

Catalog API
-----------

For usage of the ckanclient for the Catalog API, see the docs in `__init__.py`

DataStore and Data API
----------------------

Command Line Usage
``````````````````

For command line usage do::

    ./ckanclient/datastore.py -h

Client Usage
````````````

Example:

  >>> import ckanclient.datastore
  >>> data_api = 'http://thedatahub.org/api/data/fffc6388-01bc-44c4-ba0d-b860d93e6c7c'
  >>> client = ckanclient.datastore.DataStoreClient(data_api)
  >>> client.update(...)


API Keys
--------

Many operations will need your API key. This can either be set as part of the
url when conducting an operation, e.g.::

  http://{your-api-key}@thedatahub.org/api/data/fffc6388-01bc-44c4-ba0d-b860d93e6c7c'

Or you can set this in a section of your .ckanclientrc file in your home (~/)
directory::

  [index:{hostname}]
  api_key = {your-api-key}

For example::

  [index:thedatahub.org]
  api_key = adfakjfafdkjda

  [index:localhost]
  api_key = tester




Install
=======

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
