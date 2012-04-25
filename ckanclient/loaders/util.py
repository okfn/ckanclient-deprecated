#!/usr/bin/python
''' High-level utility functions.
'''

import ckanclient, os, httplib, mimetypes, urlparse, hashlib
from datetime import datetime

def post_multipart(host, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.

    Taken from http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
    """
    content_type, body = encode_multipart_formdata(fields, files)

    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    return errcode, errmsg, headers, h.file.read()

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance

    Taken from http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
    """
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
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def upload_file (client, file_path):
    """ Upload a file via the filestore api to a CKAN instance. 
    
    A timestamped directory is created on the server to store the file as
    if it had been uploaded via the graphical interface. On success, the
    url of the file is returned along with an empty error message. On failure,
    the url is an empty string.

    Arguments:
    client: a ckan client instance.
    file_path: location of the file on the local filesystem.

    Return:
    url: url of the file on the ckan server.
    errmsg: error message from the server.
    """
    c = client
    # see ckan/public/application.js:makeUploadKey for why the file_key
    # is derived this way.
    ts = datetime.isoformat(datetime.now()).replace(':','').split('.')[0]
    norm_name  = os.path.basename(file_path).replace(' ', '-')    
    file_key = os.path.join(ts, norm_name)

    auth_dict = c.storage_auth_get('/form/'+file_key, {})

    u = urlparse.urlparse(auth_dict['action'])
    fields = [('key', file_key)]
    files  = [('file', os.path.basename(file_key), open(file_path).read())]
    errcode, errmsg, headers, body = post_multipart(u.hostname, u.path, fields, files)

    if errcode == 200:
        return 'http://%s/storage/f/%s' % (u.netloc, file_key), ''
    else:
        return '', errmsg

def add_package_resource (client, package_name, file_path_or_url, **kwargs):
    """ Add file or url as a resource to a package.

    If the resource is a local file, it will be uploaded to the ckan server first.
    A dictionary representing the resource is constructed.
    The package entity is fetched from the server and the dictionary
    is appended to the list of resources. The modified package entity is put
    back on the server.

    Arguments:
    client: a ckan client instancer
    package_name: name of the package/dataset
    file_path_or_url: path of a local file or a http url.
    kwargs: optional keyword arguments are added to the resource dictionary verbatim.

    Return:
    package_entity: the package entity dictionary as return by the server.

    examples:

    >>> add_package_resource(client, 'mypkg', '/path/to/local/file', resource_type='data', description='...')
    >>> add_package_resource(client, 'mypkg', 'http://example.org/foo.txt', name='Foo', resource_type='metadata', format='csv')

    """
    c = client 
    file_path, url = '', ''

    try:
        st = os.stat(file_path_or_url)
        file_path = file_path_or_url
    except OSError, e:
        url = file_path_or_url

    if file_path:
        m = hashlib.md5(open(file_path).read())
        url, msg = upload_file(c, file_path)

        server_path = urlparse.urlparse(url).path
        if server_path.count('/') > 2:
            norm_name = '/'.join(server_path.split('/')[-2:])
        else:
            norm_name = server_path.strip('/')

        r = dict(name=norm_name, mimetype=get_content_type(file_path), hash=m.hexdigest(),
                size=st.st_size, url=url)
    else:
        r = dict(url=url)

    r.update(kwargs)
    if not r.has_key('name'): r['name'] = url

    p = c.package_entity_get(package_name)
    p['resources'].append(r)
    return c.package_entity_put(p)
