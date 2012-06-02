#!/usr/bin/env python
'''Library and command line client for the CKAN Datastore (written in Python).

For command line usage do::

    ./datastore/client.py -h

Note that CKAN DataStore is, in essence, ElasticSearch so you can use any
ElasticSearch client (http://www.elasticsearch.org/guide/appendix/clients.html)
to interact with it.
'''
import os
os.environ['http_proxy'] = ''
import urlparse
import mimetypes
import os
import ConfigParser
import urllib2
import json
import csv
import time
import logging

logger = logging.getLogger('datastore.client')


class DataStoreClient:
    def __init__(self, url):
        url = url.rstrip('/')
        self.parsed = urlparse.urlparse(url)
        newparsed = list(self.parsed)
        username = self.parsed.username
        self.netloc = self.parsed.netloc
        if username:
            # get rid of username:password@ in netloc
            self.netloc = self.parsed.netloc.split('@')[1]
            newparsed[1] = self.netloc
        if self.parsed.path.startswith('/dataset'):
            newparsed[2] = '/api/data/%s' % self.parsed.path.rstrip('/').split('/')[-1]
        self.url = urlparse.urlunparse(newparsed)
        # elastic search type name
        self.es_type_name = self.parsed.path.split('/')[-1] 
        self._setup_authorization(username)

    def query(self, query):
        '''Perform a query on ElasticSearch endpoint.
        
        :param query: a dictionary specifying the elasticsearch query as per
        elastic search spec.
        '''
        url = self.url + '/_search'
        q = json.dumps(query)
        req = urllib2.Request(url, q, self._headers)
        try:
            out = urllib2.urlopen(req).read()
        except Exception, inst:
            logger.error('%s: %s' % (inst.url, inst.read()))
            raise
        return json.loads(out)

    def upsert(self, dict_iterator, refresh=False):
        '''Insert / update documents provided in dict_iterator.'''
        start = time.time()
        url = self.url + '/_bulk'
        if refresh:
            url += '?refresh=true'

        def send_request(data):
            post_data = "%s%s" % ("\n".join(data), "\n")
            req = urllib2.Request(url, post_data, self._headers)
            return urllib2.urlopen(req)

        data = []
        for count,dict_ in enumerate(dict_iterator):
            bulkmeta = {"index": {}}
            if 'id' in dict_: bulkmeta['index']['_id'] = dict_['id']
            data.append(json.dumps(bulkmeta))
            data.append(json.dumps(dict_))
            if (count % 100) == 0:
                response = send_request(data)
                data[:] = []
                logger.debug('%s %s' % (count, (time.time() - start)))
        if data:
            send_request(data)
            logger.debug('%s %s' % (count, (time.time() - start)))

    def upload(self, filepath_or_fileobj, filetype=None, **kwargs):
        '''Upload data to webstore table. Additional required arguments is file path
        with data to upload and optional {filetype} giving type of file.
        '''
        fileobj = filepath_or_fileobj
        if isinstance(filepath_or_fileobj, basestring):
            if not filetype:
                filetype = mimetypes.guess_type(filepath_or_fileobj)[0]
            fileobj = open(filepath_or_fileobj)
        if filetype.endswith('csv'):
            self.upsert(csv.DictReader(fileobj))
        elif filetype.endswith('json'):
            self.upsert(json.load(fileobj))
        else: 
            raise ValueError('Unsupported format: %s' % filetype)

    def delete(self):
        '''Delete this DataStore table.'''
        logger.debug('DELETE: %s' % self.url)
        out = self._request(self.url, None, 'DELETE')
        logger.debug('DELETE: %s' % out)
        return out

    def mapping(self):
        '''Get the mapping for this DataStore table.'''
        url = self.url + '/_mapping'
        req = urllib2.Request(url, None, self._headers)
        data = urllib2.urlopen(req).read()
        data = json.loads(data)
        return data

    def mapping_update(self, mapping):
        '''Update the mapping for this DataStore table.
        
        @param mapping: mapping dict for this type as per
        http://www.elasticsearch.org/guide/reference/api/admin-indices-put-mapping.html

        Note that you need not (and should not) include the type name, i.e. we
        will PUT to mapping API:

        {type-name}: {mapping}
        '''
        url = self.url + '/_mapping'
        data = json.dumps({self.es_type_name: mapping})
        try:
            out = self._request(url, data, 'PUT')
        except Exception, inst:
            logger.error('%s: %s' % (inst.url, inst.read()))
            raise
        logger.debug('%s: %s' % (url, out))
        return out
        
    def _request(self, url, data, method):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url, data, self._headers)
        request.get_method = lambda: method
        response = opener.open(request)
        return response.read()

    def _setup_authorization(self, username, password=None):
        '''Get authorization field for authorization header.
        
        If password is None we assume username is in fact API key.
        '''
        if username and password:
            secret = username + ':' + password
            self.authorization = 'Basic ' + secret.encode('base64')
        elif username: # API key
            self.authorization = username
        else:
            self.authorization = self._get_api_key_from_config()
        self._headers = {}
        if self.authorization:
            self._headers['Authorization'] = self.authorization

    def _get_api_key_from_config(self):
        config_path = os.path.join(os.path.expanduser('~'), '.ckanclientrc')
        if os.path.exists(config_path):
            cfgparser = ConfigParser.SafeConfigParser()
            cfgparser.readfp(open(config_path))
            section = 'index:%s' % self.netloc
            if cfgparser.has_section(section):
                api_key = cfgparser.get(section, 'api_key', '')
                return api_key

## ======================================
## Command line interface

import sys
import inspect
import optparse
def _object_methods(obj):
    methods = inspect.getmembers(obj, inspect.ismethod)
    methods = filter(lambda (name,y): not name.startswith('_'), methods)
    methods = dict(methods)
    return methods

def _main(functions_or_object, option_list=None):
    isobject = inspect.isclass(functions_or_object)
    if isobject:
        _methods = _object_methods(functions_or_object)
    else:
        _methods = _module_functions(functions_or_object)

    usage = '''%prog {action} {table-url} [additional-arguments]

table-url is CKAN resource or webstore table url

Actions:
    '''
    usage += '\n    '.join(
        [ '%s: %s' % (name, m.__doc__ if m.__doc__ else '') for (name,m)
        in sorted(_methods.items()) ])
    parser = optparse.OptionParser(usage, option_list=option_list)
    options, args = parser.parse_args()

    if not len(args) >= 2 or not args[0] in _methods:
        parser.print_help()
        sys.exit(1)

    method = args[0]
    url = args[1]
    optdict = options.__dict__
    if isobject:
        getattr(functions_or_object(url), method)(*args[2:], **optdict)
    else:
        _methods[method](*args[1:], **optdict)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    _main(DataStoreClient)

