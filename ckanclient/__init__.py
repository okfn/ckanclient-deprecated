__version__ = '0.9'
__description__ = 'The CKAN client Python package.'
__long_description__ = \
'''The CKAN client software may be used to make requests on the Comprehensive
Knowledge Archive Network (CKAN) API including its REST interface to all
primary objects (packages, groups, tags) and its search interface.

Synopsis
========

The simplest way to make CKAN requests is:

    import ckanclient

    # Instantiate the CKAN client.
    ckan = ckanclient.CkanClient(api_key=my_key)
    
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

Changelog
=========

v0.9 2011-08-09
---------------

  * Default URL changed to thedatahub.org
  * Guard against 301 redirection, which loses POST contents


v0.8 2011-07-20
---------------

  * More detailed exceptions added
  * Some Python 3 compatibility
  

v0.7 2011-01-27
---------------

  * Package search returns results as a generator
    (rather than a list that needs to be paged)
  

v0.5 2010-12-15
---------------

  * Exception raised on error (more Pythonic)
  

v0.4 2010-10-07
---------------

  * Form API added
  * Package name editing
  * Groups added
  * Output can be verbose and use logger
  * Query API version
  * Sends API key via additional header
  

v0.3 2010-04-28
---------------

  * General usability improvements especially around error messages. 
  * Package Relationships added
  * Package deletion fixed
  * Changeset entities added
  * Improved httpauth (thanks to will waites)


v0.2 2009-11-05
---------------

  * Search API support added
  * Improved package support to include additional fields such as 'extras'
  * Support tag and group entities in addition to package
  * Compatibility changes: CkanClient base_location (now should point to base
    api e.g. http://ckan.net/api rather than http://ckan.net/api/rest)


v0.1 2008-04
------------

  * Fully functional implementation for REST interface to packages
'''

__license__ = 'MIT'

import os
import re

try:
    str = unicode
    from urllib2 import (urlopen, build_opener, install_opener,
                         HTTPBasicAuthHandler,
                         HTTPPasswordMgrWithDefaultRealm,
                         Request,
                         HTTPError, URLError)
    from urllib import urlencode
except NameError:
    # Forward compatibility with Py3k
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
    from urllib.request import (build_opener, install_opener, urlopen,
                                HTTPPasswordMgrWithDefaultRealm,
                                HTTPBasicAuthHandler,
                                Request)

try: # since python 2.6
    import json
except ImportError:
    import simplejson as json

import logging
logger = logging.getLogger('ckanclient')

PAGE_SIZE = 10

class CkanApiError(Exception): pass
class CkanApiNotFoundError(CkanApiError): pass
class CkanApiNotAuthorizedError(CkanApiError): pass
class CkanApiConflictError(CkanApiError): pass


class ApiRequest(Request):
    def __init__(self, url, data=None, headers={}, method=None):
        Request.__init__(self, url, data, headers)
        self._method = method
        
    def get_method(self):
        if self.has_data():
            if not self._method:
                return 'POST'
            assert self._method in ('POST', 'PUT'), 'Invalid method "%s" for request with data.' % self._method
            return self._method
        else:
            if not self._method:
                return 'GET'
            assert self._method in ('GET', 'DELETE'), 'Invalid method "%s" for request without data.' % self._method
            return self._method


class ApiClient(object):

    def reset(self):
        self.last_location = None
        self.last_status = None
        self.last_body = None
        self.last_headers = None
        self.last_message = None
        self.last_http_error = None
        self.last_url_error = None

    def open_url(self, location, data=None, headers={}, method=None):
        if self.is_verbose:
            self._print("ckanclient: Opening %s" % location)
        self.last_location = location
        try:
            if data != None:
                data = urlencode({data: 1})
            req = ApiRequest(location, data, headers, method=method)
            self.url_response = urlopen(req)
            if data and self.url_response.geturl() != location:
                redirection = '%s -> %s' % (location, self.url_response.geturl())
                raise URLError("Got redirected to another URL, which does not work with POSTS. Redirection: %s" % redirection)
        except HTTPError, inst:
            self._print("ckanclient: Received HTTP error code from CKAN resource.")
            self._print("ckanclient: location: %s" % location)
            self._print("ckanclient: response code: %s" % inst.fp.code)
            self._print("ckanclient: request headers: %s" % headers)
            self._print("ckanclient: request data: %s" % data)
            self._print("ckanclient: error: %s" % inst)
            self.last_http_error = inst
            self.last_status = inst.code
            self.last_message = inst.read()
        except URLError, inst:
            self._print("ckanclient: Unable to progress with URL.")
            self._print("ckanclient: location: %s" % location)
            self._print("ckanclient: request headers: %s" % headers)
            self._print("ckanclient: request data: %s" % data)
            self._print("ckanclient: error: %s" % inst)
            self.last_url_error = inst
            if isinstance(inst.reason, tuple):
                self.last_status,self.last_message = inst.reason
            else:
                self.last_message = inst.reason
                self.last_status = inst.errno
        else:
            self._print("ckanclient: OK opening CKAN resource: %s" % location)
            self.last_status = self.url_response.code
            self._print('ckanclient: last status %s' % self.last_status)
            self.last_body = self.url_response.read()
            self._print('ckanclient: last body %s' % self.last_body)
            self.last_headers = self.url_response.headers
            self._print('ckanclient: last headers %s' % self.last_headers)
            content_type = self.last_headers['Content-Type']
            self._print('ckanclient: content type: %s' % content_type)
            is_json_response = False
            if 'json' in content_type:
                is_json_response = True
            if is_json_response:
                self.last_message = self._loadstr(self.last_body)
            else:
                self.last_message = self.last_body
            self._print('ckanclient: last message %s' % self.last_message)
    
    def get_location(self, resource_name, entity_id=None, subregister=None, entity2_id=None):
        base = self.base_location
        path = self.resource_paths[resource_name]
        if entity_id != None:
            path += '/' + entity_id
            if subregister != None:
                path += '/' + subregister
                if entity2_id != None:
                    path += '/' + entity2_id            
        return base + path

    def _dumpstr(self, data):
        return json.dumps(data)
    
    def _loadstr(self, string):
        try:
            if string == '':
                data = None
            else:
                data = json.loads(string)
        except ValueError, exception:
            msg = "Couldn't decode data from JSON string: '%s': %s" % (string, exception)
            raise ValueError, msg
        return data

    def _print(self, msg):
        '''Print depending on self.is_verbose and log at the same time.'''
        return
        logger.debug(msg)
        if self.is_verbose:
            print(msg)


class CkanClient(ApiClient):
    """
    Client API implementation for CKAN.

    :param base_location: default *http://thedatahub.org/api*
    :param api_key: default *None*
    :param is_verbose: default *False*
    :param http_user: default *None*
    :param http_pass: default *None*
    """
    base_location = 'http://thedatahub.org/api'
    resource_paths = {
        'Base': '',
        'Changeset Register': '/rest/changeset',
        'Changeset Entity': '/rest/changeset',
        'Package Register': '/rest/package',
        'Package Entity': '/rest/package',
        'Tag Register': '/rest/tag',
        'Tag Entity': '/rest/tag',
        'Group Register': '/rest/group',
        'Group Entity': '/rest/group',
        'Package Search': '/search/package',
        'Package Create Form': '/form/package/create',
        'Package Edit Form': '/form/package/edit',
    }

    def __init__(self, base_location=None, api_key=None, is_verbose=False,
                 http_user=None, http_pass=None):
        if base_location is not None:
            self.base_location = base_location
        self.api_key = api_key
        self.is_verbose = is_verbose
        if http_user and http_pass:
            password_mgr = HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, base_location,
                                      http_user, http_pass)
            handler = HTTPBasicAuthHandler(password_mgr)
            opener = build_opener(handler)
            install_opener(opener)

    def _auth_headers(self):
        return {
            'Authorization': self.api_key,
            'X-CKAN-API-Key': self.api_key
            }

    def open_url(self, url, *args, **kwargs):
        result = super(CkanClient, self).open_url(url, *args, **kwargs)
        if self.last_status not in (200, 201):
            if self.last_status == 404:
                raise CkanApiNotFoundError(self.last_status)
            elif self.last_status == 403:
                raise CkanApiNotAuthorizedError(self.last_status)
            elif self.last_status == 409:
                raise CkanApiConflictError(self.last_status)
            else:
                raise CkanApiError(self.last_message)
        return result
            
    def api_version_get(self):
        self.reset()
        url = self.get_location('Base')
        self.open_url(url)
        version = self.last_message['version']
        return version    


    #
    # Model API
    #

    def package_register_get(self):
        self.reset()
        url = self.get_location('Package Register')
        self.open_url(url)
        return self.last_message

    def package_register_post(self, package_dict):
        self.reset()
        url = self.get_location('Package Register')
        data = self._dumpstr(package_dict)
        headers = self._auth_headers()
        self.open_url(url, data, headers)
        return self.last_message

    def package_entity_get(self, package_name):
        self.reset()
        url = self.get_location('Package Entity', package_name)
        headers = self._auth_headers()
        self.open_url(url, headers=headers)
        return self.last_message

    def package_entity_put(self, package_dict, package_name=None):
        # You only need to specify the current package_name if you
        # are giving it a new package_name in the package_dict.
        self.reset()
        if not package_name:
            package_name = package_dict['name']
        url = self.get_location('Package Entity', package_name)
        data = self._dumpstr(package_dict)
        headers = self._auth_headers()
        self.open_url(url, data, headers, method='PUT')
        return self.last_message

    def package_entity_delete(self, package_name):
        self.reset()
        url = self.get_location('Package Register', package_name)
        headers = self._auth_headers()
        self.open_url(url, headers=headers, method='DELETE')
        return self.last_message

    def package_relationship_register_get(self, package_name,
                relationship_type='relationships', 
                relationship_with_package_name=None):
        self.reset()
        url = self.get_location('Package Entity',
           entity_id=package_name,
           subregister=relationship_type,
           entity2_id=relationship_with_package_name)
        headers = self._auth_headers()
        self.open_url(url, headers=headers)
        return self.last_message

    def package_relationship_entity_post(self, subject_package_name,
                relationship_type, object_package_name, comment=u''):
        self.reset()
        url = self.get_location('Package Entity',
            entity_id=subject_package_name,
            subregister=relationship_type,
            entity2_id=object_package_name)
        data = self._dumpstr({'comment':comment})
        headers = self._auth_headers()
        self.open_url(url, data, headers, method='POST')
        return self.last_message

    def package_relationship_entity_put(self, subject_package_name,
                relationship_type, object_package_name, comment=u''):
        self.reset()
        url = self.get_location('Package Entity',
            entity_id=subject_package_name,
            subregister=relationship_type,
            entity2_id=object_package_name)
        data = self._dumpstr({'comment':comment})
        headers = self._auth_headers()
        self.open_url(url, data, headers, method='PUT')
        return self.last_message

    def package_relationship_entity_delete(self, subject_package_name,
                relationship_type, object_package_name):
        self.reset()
        url = self.get_location('Package Entity',
            entity_id=subject_package_name,
            subregister=relationship_type,
            entity2_id=object_package_name)
        headers = self._auth_headers()
        self.open_url(url, headers=headers, method='DELETE')
        return self.last_message

    def tag_register_get(self):
        self.reset()
        url = self.get_location('Tag Register')
        self.open_url(url)
        return self.last_message

    def tag_entity_get(self, tag_name):
        self.reset()
        url = self.get_location('Tag Entity', tag_name)
        self.open_url(url)
        return self.last_message

    def group_register_post(self, group_dict):
        self.reset()
        url = self.get_location('Group Register')
        data = self._dumpstr(group_dict)
        headers = self._auth_headers()
        self.open_url(url, data, headers)
        return self.last_message

    def group_register_get(self):
        self.reset()
        url = self.get_location('Group Register')
        self.open_url(url)
        return self.last_message

    def group_entity_get(self, group_name):
        self.reset()
        url = self.get_location('Group Entity', group_name)
        self.open_url(url)
        return self.last_message

    def group_entity_put(self, group_dict, group_name=None):
        # You only need to specify the current group_name if you
        # are giving it a new group_name in the group_dict.
        self.reset()
        if not group_name:
            group_name = group_dict['name']
        url = self.get_location('Group Entity', group_name)
        data = self._dumpstr(group_dict)
        headers = self._auth_headers()
        self.open_url(url, data, headers, method='PUT')
        return self.last_message

    #
    # Search API
    #

    def package_search(self, q, search_options=None):
        self.reset()
        search_options = search_options.copy() if search_options else {}
        url = self.get_location('Package Search')
        search_options['q'] = q
        if not search_options.get('limit'):
            search_options['limit'] = PAGE_SIZE
        data = self._dumpstr(search_options)
        headers = self._auth_headers()
        self.open_url(url, data, headers)
        result_dict = self.last_message
        if not search_options.get('offset'):
            result_dict['results'] = self._result_generator(result_dict['count'], result_dict['results'], self.package_search, q, search_options)
        return result_dict

    def _result_generator(self, count, results, func, q, search_options):
        '''Returns a generator that will make the necessary calls to page
        through results.'''
        page = 0
        num_pages = int(count / search_options['limit'] + 0.9999)
        while True:
            for res in results:
                yield res

            # go to next page?
            page += 1
            if page >= num_pages:
                break

            # retrieve next page
            search_options['offset'] = page * search_options['limit']
            result_dict = func(q, search_options)
            results = result_dict['results']
            
    #
    # Form API
    #

    def package_create_form_get(self):
        self.reset()
        url = self.get_location('Package Create Form')
        self.open_url(url)
        return self.last_message

    def package_create_form_post(self, form_submission):
        self.reset()
        url = self.get_location('Package Create Form')
        data = self._dumpstr(form_submission)
        headers = self._auth_headers()
        self.open_url(url, data, headers)
        return self.last_message

    def package_edit_form_get(self, package_ref):
        self.reset()
        url = self.get_location('Package Edit Form', package_ref)
        self.open_url(url)
        return self.last_message

    def package_edit_form_post(self, package_ref, form_submission):
        self.reset()
        url = self.get_location('Package Edit Form', package_ref)
        data = self._dumpstr(form_submission)
        headers = self._auth_headers()
        self.open_url(url, data, headers)
        return self.last_message

    #
    # Changeset API
    #
    
    def changeset_register_get(self):
        self.reset()
        url = self.get_location('Changeset Register')
        self.open_url(url)
        return self.last_message

    def changeset_entity_get(self, changeset_name):
        self.reset()
        url = self.get_location('Changeset Entity', changeset_name)
        self.open_url(url)
        return self.last_message

    #
    # data API
    #
    def _storage_metadata_url(self, path):
        url = self.base_location
        if not url.endswith("/"): url += "/"
        url += "storage/metadata"
        if not path.startswith("/"): url += "/"
        url += path
        return url
    def storage_metadata_get(self, path):
        url = self._storage_metadata_url(path)
        self.open_url(url)
        return self._loadstr(self.last_message)
    def storage_metadata_set(self, path, metadata):
        url = self._storage_metadata_url(path)
        payload = self._dumpstr(metadata)
        self.open_url(url, payload, method="PUT")
        return self._loadstr(self.last_message)
    def storage_metadata_update(self, path, metadata):
        url = self._storage_metadata_url(path)
        payload = self._dumpstr(metadata)
        self.open_url(url, payload, method="POST")
        return self._loadstr(self.last_message)

    def _storage_auth_url(self, path):
        url = self.base_location
        if not url.endswith("/"): url += "/"
        url += "storage/auth"
        if not path.startswith("/"): url += "/"
        url += path
        return url
    def storage_auth_get(self, path, headers):
        url = self._storage_auth_url(path)
        payload = self._dumpstr(headers)
        self.open_url(url, payload, method="POST")
        return self._loadstr(self.last_message)
    
    #
    # Utils
    #
    def is_id(self, id_string):
        '''Tells the client if the string looks like an id or not'''
        return bool(re.match('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', id_string))
