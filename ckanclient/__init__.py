__version__ = '0.1'
__description__ = 'The CKAN client Python package.'
__long_description__ = \
'''The CKAN client software may be used to make requests on the Comprehensive
Knowledge Archive Network (CKAN) REST API.

## Synopsis ##

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
'''

__license__ = 'MIT'

import os, urllib, urllib2
import logging
logger = logging.getLogger('ckanclient')

class CkanClient(object):
    
    base_location = 'http://www.ckan.net/api'
    resource_paths = {
        'Base': '/',
        'Package Register': '/rest/package',
        'Package Entity': '/rest/package',
        'Tag Register': '/rest/tag',
        'Tag Entity': '/rest/tag',
        'Group Register': '/rest/group',
        'Group Entity': '/rest/group',
        'Package Search': '/search/package',
    }

    def __init__(self, base_location=None, api_key=None):
        if base_location is not None:
            self.base_location = base_location
        self.api_key = api_key

    def reset(self):
        self.last_status = None
        self.last_body = None
        self.last_headers = None
        self.last_message = None
        self.last_http_error = None
        self.last_url_error = None

    def open_url(self, location, data=None, headers={}):
        try:
            if data != None:
                data = urllib.urlencode({data: 1}) 
            req = urllib2.Request(location, data, headers)
            self.url_response = urllib2.urlopen(req)
        except urllib2.HTTPError, inst:
            #print "ckanclient: Received HTTP error code from CKAN resource."
            #print "ckanclient: location: %s" % location
            #print "ckanclient: response code: %s" % inst.fp.code
            #print "ckanclient: request headers: %s" % headers
            #print "ckanclient: request data: %s" % data
            self.last_http_error = inst
            self.last_status = inst.fp.code
        except urllib2.URLError, inst:
            self.last_url_error = inst
        else:
            #print "ckanclient: OK opening CKAN resource: %s" % location
            self.last_status = self.url_response.code
            self.last_body = self.url_response.read()
            self.last_headers = self.url_response.headers
            try:
                self.last_message = self.__loadstr(self.last_body)
            except ValueError:
                pass
    
    def get_location(self, resource_name, entity_id=None):
        base = self.base_location
        path = self.resource_paths[resource_name]
        if entity_id != None:
            path += '/' + entity_id
        return base + path

    def open_base_location(self):
        self.reset()
        url = self.get_location('Base')
        self.open_url(self.base_location)

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
        self.open_url(url, data, headers)

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
        self.open_url(url, data, headers)

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

