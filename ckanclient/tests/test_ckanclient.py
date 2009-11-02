import ckanclient

# Todo: Discovery of local api-key for the okfntest:okfntest test user.
# Todo: Fix CKAN so that tags are created with the new package (register post).

class TestCkanClient(object):

    # Before running tests:

    #  1. Run a test server in another shell
    #  2. On the test server run:
    #      $ paster db clean && paster db init && paster create-test-data
    #  3. Login to the test server for the api-key and set these options:
    test_base_location = 'http://127.0.0.1:5000/api'
    test_api_key = '6a1940ee-1d1d-4532-9b84-4ec05b068c9d'

    def setUp(self):
        self.c = ckanclient.CkanClient(
            base_location=self.test_base_location,
            api_key=self.test_api_key,
        )

    def test_0_get_locations(self):
        rest_base = self.test_base_location + '/rest'
        search_base = self.test_base_location + '/search'
        url = self.c.get_location('Base')
        assert url == self.test_base_location + '/', url
        url = self.c.get_location('Package Register')
        assert url == rest_base + '/package'
        url = self.c.get_location('Package Entity', 'myname')
        assert url == rest_base + '/package/myname'
        url = self.c.get_location('Group Register')
        assert url == rest_base + '/group'
        url = self.c.get_location('Group Entity', 'myname')
        assert url == rest_base + '/group/myname'
        url = self.c.get_location('Tag Register')
        assert url == rest_base + '/tag'
        url = self.c.get_location('Tag Entity', 'myname')
        assert url == rest_base + '/tag/myname'
        url = self.c.get_location('Tag Entity', 'myname')
        assert url == rest_base + '/tag/myname'
        url = self.c.get_location('Package Search')
        assert url == search_base + '/package'

    def test_1_open_base_location(self):
        assert self.c.base_location == self.test_base_location
        self.c.open_base_location()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert 'REST Resources and Locations' in body
        # Not sure why this doesn't work anymore
        # header = self.c.last_headers.get('Connection')
        # assert header == 'close', self.c.last_headers

    def test_1_package_register_get(self):
        self.c.package_register_get()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert 'annakarenina' in body
        assert type(self.c.last_message) == list
        assert 'annakarenina' in self.c.last_message

    def test_1_package_entity_get(self):
        # Check registered entity is found.
        self.c.package_entity_get('annakarenina')
        status = self.c.last_status
        assert status == 200, status
        body = self.c.last_body
        assert 'annakarenina' in body
        assert self.c.last_message
        message = self.c.last_message
        assert type(message) == dict
        assert message['name'] == u'annakarenina'
        assert message['title'] == u'A Novel By Tolstoy'

        # Check unregistered entity is not found.
        self.c.package_entity_get('mycoffeecup')
        status = self.c.last_status
        assert status == 404, status

    def _generate_pkg_name(self):
        pkg_name = 'ckanclienttest'
        import time
        timestr = str(time.time()).replace('.', '')
        pkg_name += timestr
        return pkg_name

    def test_2_package_register_post(self):
        pkg_name = self._generate_pkg_name()
        # Check package isn't registered.
        self.c.package_entity_get(pkg_name)
        status = self.c.last_status
        assert status == 404, status
        # Check registration of new package.
        package = {
            'name': pkg_name,
            'url': 'orig_url',
            'download_url': 'orig_download_url',
            'tags': ['russian', 'newtag'],
            'extras': {'genre':'thriller', 'format':'ebook'},
        }
        self.c.package_register_post(package)
        status = self.c.last_status
        assert status == 200, status

        # Check package is registered.
        self.c.package_entity_get(pkg_name)
        status = self.c.last_status
        assert status == 200, status
        message = self.c.last_message
        name = message['name']
        assert name == pkg_name
        url = message['url']
        assert url == 'orig_url'
        download_url = message['download_url']
        assert download_url == 'orig_download_url'
        tags = message['tags']
        assert tags == ['russian', 'newtag']
        extras = message['extras']
        assert extras == package['extras']
        

    def test_3_package_entity_put(self):
        pkg_name = self._generate_pkg_name()
        # Register new package.
        package = {
            'name': pkg_name,
            'url': 'orig_url',
            'download_url': 'orig_download_url',
            'tags': ['russian'],
        }
        self.c.package_register_post(package)
        status = self.c.last_status
        assert status == 200, status
        
        # Check update of existing package.
        mytag = 'mytag' + pkg_name
        package = {
            'name': pkg_name,
            'url': 'new_url',
            'download_url': 'new_download_url',
            'tags': ['russian', 'tolstoy', mytag],
            'extras': {'genre':'thriller', 'format':'ebook'},
        }
        self.c.package_entity_put(package)
        status = self.c.last_status
        assert status == 200

        # Check package is updated.
        self.c.package_entity_get(pkg_name)
        status = self.c.last_status
        assert status == 200, status
        message = self.c.last_message
        name = message['name']
        assert name == pkg_name
        url = message['url']
        assert url == 'new_url'
        download_url = message['download_url']
        assert download_url == 'new_download_url'
        tags = message['tags']
        assert tags == ['russian', 'tolstoy', mytag], tags
        extras = message['extras']
        assert extras == package['extras']

    # Todo: Package entity delete.
    def test_4_package_entity_delete(self):
        pass

    def test_5_tag_register_get(self):
        self.c.tag_register_get()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert 'russian' in body
        assert type(self.c.last_message) == list
        assert 'russian' in self.c.last_message

    def test_6_pkg_search_basic(self):
        res = self.c.package_search('anna')
        status = self.c.last_status
        assert status == 200, status
        assert res['count'] == 1, res
        assert res['results'] == [u'annakarenina']
