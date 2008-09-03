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
    ckan.package_register_get()
    package_list = ckan.last_message
    print package_list

    # Get the tag list.
    ckan.tag_register_get()
    tag_list = ckan.last_message
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
    ckan.package_entity_post(package_entity)

'''

__license__ = 'MIT'

import os, urllib, urllib2
import simplejson

class CkanClient(object):
    
    base_location = 'http://www.ckan.net/api/rest'
    resource_paths = {
        'Base': '/',
        'Package Register': '/package',
        'Package Entity': '/package',
        'Tag Register': '/tag',
        'Tag Entity': '/tag',
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
                self.last_message = self.loadstr(self.last_body)
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
        data = self.dumpstr(package_dict)
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
        data = self.dumpstr(package_dict)
        headers = {'Authorization': self.api_key}
        self.open_url(url, data, headers)

    def tag_register_get(self):
        self.reset()
        url = self.get_location('Tag Register')
        self.open_url(url)
        return self.last_message

    def dumpstr(self, data):
        return simplejson.dumps(data)
    
    def loadstr(self, string):
        return simplejson.loads(string)

