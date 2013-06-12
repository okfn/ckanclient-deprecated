==========
ckanclient
==========

ckanclient is a Python library and command-line client to read and write to a
CKAN instance via the API. It supports the `CKAN API`_, the CKAN FileStore's
`Storage API`_, and the CKAN DataStore's `Data API`_.

.. _CKAN API: http://docs.ckan.org/en/latest/index.html#the-ckan-api 
.. _Storage API: http://docs.ckan.org/en/latest/filestore.html#storage-api 
.. _Data API: http://docs.ckan.org/en/latest/datastore.html

Installation
------------

Using pip::

    pip install ckanclient

You can also download releases of ckanclient directly from PyPI:

http://pypi.python.org/pypi/ckanclient

or you can get the latest development version from git::

    git clone https://github.com/okfn/ckanclient.git

Usage
-----

API Key
=======

You can either pass your API key explicitly when creating the CkanClient instance::

    client = CkanClient(api_key='my-api-key')

Or you can put your API key in your ``~/.ckanclientrc`` file::

    [index:{hostname}]
    api_key = {your-api-key}

For example::

    [index:datahub.io]
    api_key = adfakjfafdkjda

    [index:localhost]
    api_key = tester

Python Library
==============

Catalog API
```````````

ckanclient can be used to make requests to the CKAN API, including the API's
REST interface to all primary objects (datasets, groups, tags) and its search
interface.

The simplest way to make CKAN API requests is::

    import ckanclient

    # Instantiate the CKAN client.
    ckan = ckanclient.CkanClient(base_location='http://datahub.io/api',
                                 api_key='adbc-1c0d')
    # (use your own api_key from http://datahub.io/user/me )

    # Get the package list.
    package_list = ckan.package_register_get()
    print package_list

    # Get the tag list.
    tag_list = ckan.tag_register_get()
    print tag_list

    # Collect the package metadata.
    package_entity = {
        'name': my_package_name,
        'url': my_package_url,
        'download_url': my_package_download_url,
        'tags': my_package_keywords,
        'notes': my_package_long_description,
    }

    # Register the package.
    ckan.package_register_post(package_entity)

    # Get the details of a package.
    ckan.package_entity_get(package_name)
    package_entity = ckan.last_message
    print package_entity

    # Update the details of a package.
    ckan.package_entity_get(package_name)
    package_entity = ckan.last_message
    package_entity['url'] = new_package_url
    package_entity['notes'] = new_package_notes
    ckan.package_entity_put(package_entity)

    # List groups
    group_list = ckan.group_register_get()
    print group_list

    # Create a new group
    group_entity = {
        'name': my_group_name,
        'title': my_group_title,
        'description': my_group_description,
        'packages': group_package_names,
        }
    ckan.group_register_post(group_entity)

    # Get the details of a group.
    print ckan.group_entity_get(group_name)

    # Update the group details
    group_entity = ckan.last_message
    group_entity['title'] = new_group_title
    group_entity['packages'] = new_group_packages
    ckan.group_entity_put(group_entity)

FileStore and Storage API
`````````````````````````

You can use ckanclient to upload files to CKAN's FileStore via the Storage API,
example::

    import ckanclient
    ckan = ckanclient.CkanClient(base_location='http://datahub.io/api',
        api_key='aa9368b2-6f18-4c96-b190-4f3355613d88')
    ckan.upload_file('my_data.csv')
    ckan.add_package_resource('my_dataset', 'my_data_file.csv',
                resource_type='data', description='...')
    ckan.add_package_resource('my_dataset', 'http://example.org/foo.txt',
                name='Foo', resource_type='metadata', format='csv')

DataStore and Data API
``````````````````````

To be updated - read the source for the present!


Command Line Interface
======================

Install ckanclient will create a command line client named (unsurprisingly!)
`ckanclient`. To see usage do::

    ckanclient -h

Example::

    ckanclient package_entity_get ckan

You can specify the ckan site you wish to use using the --ckan option::

    ckanclient --ckan=http://datahub.io/api package_entity_get ckan

NB: the command line is currently under development.


Tests
-----

The ckanclient tests require the ckan and nose modules to be installed.
Optionally ckanext-dgu can be installed too and the form api will be tested.

To run the tests::

    nosetests --ckan ckanclient/tests
