__version__ = '0.10'
__description__ = 'Python client for the CKAN API.'
__long_description__ = \
'''The CKAN client software may be used to make requests on the Comprehensive
Knowledge Archive Network (CKAN) API including its REST interface to all
primary objects (packages, groups, tags) and its search interface.
'''
__license__ = 'MIT'

import os
import re

import httplib, mimetypes, urlparse, hashlib
from datetime import datetime

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
    try:
        import simplejson as json
    except ImportError:
        class _json(object):
            def __getattr__(self, name):
                import simplejson as json
        json = _json()

import logging
logger = logging.getLogger('ckanclient')

PAGE_SIZE = 10

class CkanApiError(Exception): pass
class CkanApiNotFoundError(CkanApiError): pass
class CkanApiNotAuthorizedError(CkanApiError): pass
class CkanApiConflictError(CkanApiError): pass
class CkanApiActionError(Exception): pass


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
        self.last_help = None # Action API only
        self.last_result = None # Action API only
        self.last_ckan_error = None # Action API only

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

    def get_action_location(self, action_name):
        return '%s/action/%s' % (self.base_location, action_name)

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
    '''Client API implementation for CKAN.

    :param base_location: default *http://thedatahub.org/api*
    :param api_key: default *None*
    :param is_verbose: default *False*
    :param http_user: default *None*
    :param http_pass: default *None*

    '''
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
            
    def open_action_url(self, url, data_dict):
        data_json = self._dumpstr(data_dict)
        result = super(CkanClient, self).open_url(url, data=data_json)
        if self.last_status not in (200, 201):
            if self.last_status == 404:
                raise CkanApiNotFoundError(self.last_status)
            elif self.last_status == 403:
                raise CkanApiNotAuthorizedError(self.last_status)
            elif self.last_status == 409:
                raise CkanApiConflictError(self.last_status)
            else:
                raise CkanApiError(self.last_message)
        self.last_help = self.last_message['help']
        if self.last_message['success']:
            self.last_result = self.last_message['result']
        else:
            self.last_ckan_error = self.last_message['error']
            raise CkanApiActionError(self.last_ckan_error)
        return self.last_result

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
        headers = self._auth_headers()
        self.open_url(url, headers=headers)
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
        headers = self._auth_headers()
        self.open_url(url, headers=headers)
        return self.last_message

    def tag_entity_get(self, tag_name):
        self.reset()
        url = self.get_location('Tag Entity', tag_name)
        headers = self._auth_headers()
        self.open_url(url, headers=headers)
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
        headers = self._auth_headers()
        self.open_url(url, headers=headers)
        return self.last_message

    def group_entity_get(self, group_name):
        self.reset()
        url = self.get_location('Group Entity', group_name)
        headers = self._auth_headers()
        self.open_url(url, headers=headers)
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
        headers = self._auth_headers()        
        self.open_url(url, headers=headers)
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
        headers = self._auth_headers()
        self.open_url(url, headers=headers)
        return self.last_message

    def package_edit_form_post(self, package_ref, form_submission):
        self.reset()
        url = self.get_location('Package Edit Form', package_ref)
        data = self._dumpstr(form_submission)
        headers = self._auth_headers()
        self.open_url(url, data, headers)
        return self.last_message

    #
    # Storage API
    #
    def _storage_metadata_url(self, path):
        url = self.base_location
        if not url.endswith("/"): url += "/"
        url += "storage/metadata"
        if not path.startswith("/"): url += "/"
        url += path
        return url

    def storage_metadata_get(self, label):
        '''Get the JSON metadata for a file that has been uploaded to CKAN's
        FileStore.

        :param label: The 'label' that identifies the file in CKAN's
        filestore. When you upload a file to the FileStore a path is
        generated for it, e.g. /storage/f/2012-04-27T092841/myfile.jpg. The
        label is just the last part of this path, e.g.
        2012-04-27T092841/myfile.jpg

        '''
        url = self._storage_metadata_url(label)
        headers = self._auth_headers()
        self.open_url(url, headers=headers)
        return self.last_message

    def storage_metadata_set(self, label, metadata):
        url = self._storage_metadata_url(label)
        payload = self._dumpstr(metadata)
        headers = self._auth_headers()
        self.open_url(url, payload, headers=headers, method="PUT")
        return self.last_message

    def storage_metadata_update(self, label, metadata):
        url = self._storage_metadata_url(label)
        payload = self._dumpstr(metadata)
        headers = self._auth_headers()
        self.open_url(url, payload, headers=headers, method="POST")
        return self.last_message

    def _storage_auth_url(self, label):
        url = self.base_location
        if not url.endswith("/"): url += "/"
        url += "storage/auth"
        if not label.startswith("/"): url += "/"
        url += label
        return url

    def storage_auth_get(self, label, headers):
        url = self._storage_auth_url(label)
        payload = self._dumpstr(headers)
        headers = self._auth_headers()
        self.open_url(url, payload, headers=headers, method="POST")
        return self.last_message

    #
    # Action API
    #

    # for any action
    def action(self, action_name, **kwargs):
        self.reset()
        url = self.get_action_location(action_name)
        self.open_action_url(url, kwargs)
        return self.last_result

    def package_list(self):
        return self.action('package_list')
        
    def package_show(self, package_id):
        return self.action('package_show', id=package_id)

    def status_show(self):
        return self.action('status_show')

    def ckan_version(self):
        return self.action('status_show')['ckan_version']

    #
    # Private Helpers
    #
    def _post_multipart(self, selector, fields, files):
        '''Post fields and files to an http host as multipart/form-data.

        Taken from
        http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/

        :param fields: a sequence of (name, value) tuples for regular form
            fields
        :param files: a sequence of (name, filename, value) tuples for data to
            be uploaded as files

        :returns: the server's response page

        '''
        content_type, body = self._encode_multipart_formdata(fields, files)

        h = httplib.HTTP(urlparse.urlparse(self.base_location).netloc)
        h.putrequest('POST', selector)
        h.putheader('content-type', content_type)
        h.putheader('content-length', str(len(body)))
        h.endheaders()
        h.send(body)
        errcode, errmsg, headers = h.getreply()
        return errcode, errmsg, headers, h.file.read()

    def _encode_multipart_formdata(self, fields, files):
        '''Encode fields and files to be posted as multipart/form-data.

        Taken from
        http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/

        :param fields: a sequence of (name, value) tuples for the regular
            form fields to be encoded
        :param files: a sequence of (name, filename, value) tuples for the data
            to be uploaded as files

        :returns: (content_type, body) ready for httplib.HTTP instance

        '''
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % self._get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def _get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    #
    # CkanClient utils
    #
    def is_id(self, id_string):
        '''Tells the client if the string looks like an id or not'''
        return bool(re.match('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', id_string))

    def upload_file (self, file_path):
        '''Upload a file to a CKAN instance via CKAN's FileStore API.

        The CKAN instance must have file storage enabled.

        A timestamped directory is created on the server to store the file as
        if it had been uploaded via the graphical interface. On success, the
        URL of the file is returned along with an empty error message. On
        failure, the URL is an empty string.

        :param file_path: path to the file to upload, on the local filesystem
        :type file_path: string

        :returns: a (url, errmsg) 2-tuple containing the URL of the
            successufully uploaded file on the CKAN server (string, an empty
            string if the upload failed) and any error message from the server
            (string, an empty string if there was no error)
        :rtype: (string, string) 2-tuple

        '''
        # see ckan/public/application.js:makeUploadKey for why the file_key
        # is derived this way.
        ts = datetime.isoformat(datetime.now()).replace(':','').split('.')[0]
        norm_name  = os.path.basename(file_path).replace(' ', '-')
        file_key = os.path.join(ts, norm_name)

        auth_dict = self.storage_auth_get('/form/'+file_key, {})

        u = urlparse.urlparse(auth_dict['action'])
        fields = [('key', file_key)]
        files  = [('file', os.path.basename(file_key), open(file_path).read())]
        errcode, errmsg, headers, body = self._post_multipart(u.path, fields,
                files)

        if errcode == 200:
            return 'http://%s/storage/f/%s' % (u.netloc, file_key), ''
        else:
            return '', errmsg

    def add_package_resource (self, package_name, file_path_or_url, **kwargs):
        '''Add a file or URL to a dataset (package) as a resource.

        If the resource is a local file then the CKAN instance must have file
        storage enabled. The file will be uploaded to the CKAN server.

        A dictionary representing the resource is constructed. The package is
        fetched from the server and the dictionary is appended to the package's
        list of resources. The modified package is put back on the server.
        examples:

        >>> client.add_package_resource('mypkg', '/path/to/local/file',
                resource_type='data', description='...')
        >>> client.add_package_resource('mypkg', 'http://example.org/foo.txt',
                name='Foo', resource_type='metadata', format='csv')

        :param package_name: the name of the dataset (package) to upload to
        :type package_name: string
        :param file_path_or_url: local filesystem path or URL of the file to
            add
        :type file_path_or_url: string
        :param kwargs: arbitrary keyword arguments to add to the resource
            dictionary verbatim (optional)

        :returns: the modified dataset dictionary as returned by the server
        :rtype: dataset dictionary

        '''
        file_path, url = '', ''

        try:
            st = os.stat(file_path_or_url)
            file_path = file_path_or_url
        except OSError, e:
            url = file_path_or_url

        if file_path:
            m = hashlib.sha1(open(file_path).read())
            url, msg = self.upload_file(file_path)
            urlp = urlparse.urlparse(url)

            server_path = urlp.path
            if server_path.count('/') > 2:
                norm_name = '/'.join(server_path.split('/')[-2:])
            else:
                norm_name = server_path.strip('/')

            r = dict(name=norm_name,
                    mimetype=self._get_content_type(file_path),
                    hash=m.hexdigest(), size=st.st_size, url=server_path)
        else:
            r = dict(url=url)

        r.update(kwargs)
        if not r.has_key('name'): r['name'] = url

        p = self.package_entity_get(package_name)
        p['resources'].append(r)
        return self.package_entity_put(p)
