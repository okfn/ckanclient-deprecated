__version__ = '0.3'
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

import os, urllib, urllib2
import logging
logger = logging.getLogger('ckanclient')

class CkanClient(object):
    
    base_location = 'http://www.ckan.net/api'
    resource_paths = {
        'Base': '/',
        'Changeset Register': '/rest/changeset',
        'Changeset Entity': '/rest/changeset',
        'Package Register': '/rest/package',
        'Package Entity': '/rest/package',
        'Tag Register': '/rest/tag',
        'Tag Entity': '/rest/tag',
        'Group Register': '/rest/group',
        'Group Entity': '/rest/group',
        'Package Search': '/search/package',
    }

    def __init__(self, base_location=None, api_key=None, is_verbose=False,
                 http_user=None, http_pass=None):
        if base_location is not None:
            self.base_location = base_location
        self.api_key = api_key
        self.is_verbose = is_verbose
        if http_user and http_pass:
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, base_location,
                                      http_user, http_pass)
            handler = urllib2.HTTPBasicAuthHandler(password_mgr)
            opener = urllib2.build_opener(handler)
            urllib2.install_opener(opener)

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
            print "ckanclient: Opening %s" % location
        self.last_location = location
        try:
            if data != None:
                data = urllib.urlencode({data: 1})
            req = Request(location, data, headers, method=method)
            self.url_response = urllib2.urlopen(req)
        except urllib2.HTTPError, inst:
            if self.is_verbose:
                print "ckanclient: Received HTTP error code from CKAN resource."
                print "ckanclient: location: %s" % location
                print "ckanclient: response code: %s" % inst.fp.code
                print "ckanclient: request headers: %s" % headers
                print "ckanclient: request data: %s" % data
                print "ckanclient: error: %s" % inst
            self.last_http_error = inst
            self.last_status = inst.code
            self.last_message = inst.read()
        except urllib2.URLError, inst:
            if self.is_verbose:
                print "ckanclient: Unable to progress with URL."
                print "ckanclient: location: %s" % location
                print "ckanclient: request headers: %s" % headers
                print "ckanclient: request data: %s" % data
                print "ckanclient: error: %s" % inst
            self.last_url_error = inst
            self.last_status,self.last_message = inst.reason
        else:
            if self.is_verbose:
                print "ckanclient: OK opening CKAN resource: %s" % location
            self.last_status = self.url_response.code
            self.last_body = self.url_response.read()
            self.last_headers = self.url_response.headers
            try:
                self.last_message = self.__loadstr(self.last_body)
            except ValueError:
                pass
    
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

    def open_base_location(self):
        self.reset()
        url = self.get_location('Base')
        self.open_url(self.base_location)

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

    def package_register_get(self):
        self.reset()
        url = self.get_location('Package Register')
        self.open_url(url)
        return self.last_message

    def package_register_post(self, package_dict):
        self.reset()
        url = self.get_location('Package Register')
        data = self.__dumpstr(package_dict)
        headers = {'Authorization': self.api_key}
        self.open_url(url, data, headers)

    def package_entity_get(self, package_name):
        self.reset()
        url = self.get_location('Package Entity', package_name)
        self.open_url(url)
        return self.last_message

    def package_entity_put(self, package_dict):
        self.reset()
        package_name = package_dict['name']
        url = self.get_location('Package Entity', package_name)
        data = self.__dumpstr(package_dict)
        headers = {'Authorization': self.api_key}
        self.open_url(url, data, headers, method='PUT')

    def package_entity_delete(self, package_name):
        self.reset()
        url = self.get_location('Package Register', package_name)
        headers = {'Authorization': self.api_key}
        self.open_url(url, headers=headers, method='DELETE')

    def package_relationship_register_get(self, package_name,
                relationship_type='relationships', 
                relationship_with_package_name=None):
        self.reset()
        url = self.get_location('Package Entity',
           entity_id=package_name,
           subregister=relationship_type,
           entity2_id=relationship_with_package_name)
        headers = {'Authorization': self.api_key}
        self.open_url(url, headers=headers)
        return self.last_message

    def package_relationship_entity_post(self, subject_package_name,
                relationship_type, object_package_name, comment=u''):
        self.reset()
        url = self.get_location('Package Entity',
            entity_id=subject_package_name,
            subregister=relationship_type,
            entity2_id=object_package_name)
        data = self.__dumpstr({'comment':comment})
        headers = {'Authorization': self.api_key}
        self.open_url(url, data, headers, method='POST')

    def package_relationship_entity_put(self, subject_package_name,
                relationship_type, object_package_name, comment=u''):
        self.reset()
        url = self.get_location('Package Entity',
            entity_id=subject_package_name,
            subregister=relationship_type,
            entity2_id=object_package_name)
        data = self.__dumpstr({'comment':comment})
        headers = {'Authorization': self.api_key}
        self.open_url(url, data, headers, method='PUT')

    def package_relationship_entity_delete(self, subject_package_name,
                relationship_type, object_package_name):
        self.reset()
        url = self.get_location('Package Entity',
            entity_id=subject_package_name,
            subregister=relationship_type,
            entity2_id=object_package_name)
        headers = {'Authorization': self.api_key}
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
        data = self.__dumpstr(group_dict)
        headers = {'Authorization': self.api_key}
        self.open_url(url, data, headers)

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

    def group_entity_put(self, group_dict):
        self.reset()
        group_name = group_dict['name']
        url = self.get_location('Group Entity', group_name)
        data = self.__dumpstr(group_dict)
        headers = {'Authorization': self.api_key}
        self.open_url(url, data, headers, method='PUT')

    def package_search(self, q, search_options={}):
        self.reset()
        url = self.get_location('Package Search')
        search_options['q'] = q
        data = self.__dumpstr(search_options)
        headers = {'Authorization': self.api_key}
        self.open_url(url, data, headers)
        return self.last_message

    def __dumpstr(self, data):
        try: # since python 2.6
            import json
        except ImportError:
            import simplejson as json
        return json.dumps(data)
    
    def __loadstr(self, string):
        try: # since python 2.6
            import json
        except ImportError:
            import simplejson as json
        return json.loads(string)


class Request(urllib2.Request):
    def __init__(self, url, data=None, headers={}, method=None):
        urllib2.Request.__init__(self, url, data, headers)
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
            
                

