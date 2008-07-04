import ckanclient

class TestCkanClient(object):

    test_base_location = 'http://127.0.0.1:5000/api/rest'
    test_api_key = '5f7a1710-67a2-4afa-97e7-0d1f3e9b52df'

    def setUp(self):
        self.c = ckanclient.CkanClient(
            base_location=self.test_base_location,
            api_key=self.test_api_key,
        )

    def test_get_locations(self):
        url = self.c.get_location('Base')
        assert url == self.test_base_location + '/'
        url = self.c.get_location('Package Register')
        assert url == self.test_base_location + '/package'
        url = self.c.get_location('Package Entity', 'myname')
        assert url == self.test_base_location + '/package/myname'
        url = self.c.get_location('Tag Register')
        assert url == self.test_base_location + '/tag'
        url = self.c.get_location('Tag Entity', 'myname')
        assert url == self.test_base_location + '/tag/myname'

    def test_open_base_location(self):
        assert self.c.base_location == self.test_base_location
        self.c.open_base_location()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert 'Methods, Data Formats, Status Codes' in body
        header = self.c.last_headers.get('Connection')
        assert header == 'close'

    def test_package_register_get(self):
        self.c.package_register_get()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert 'annakarenina' in body
        assert type(self.c.last_message) == list
        assert 'annakarenina' in self.c.last_message

    def test_package_entity_get(self):
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

    def generate_pkg_name(self):
        pkg_name = 'ckanclienttest'
        import time
        timestr = str(time.time()).replace('.', '')
        pkg_name += timestr
        return pkg_name

    def test_package_register_post(self):
        pkg_name = self.generate_pkg_name()
        # Check package isn't registered.
        self.c.package_entity_get(pkg_name)
        status = self.c.last_status
        assert status == 404, status
        # Check registration of new package.
        package = {
            'name': pkg_name,
            'url': 'orig_url',
            'download_url': 'orig_download_url',
            'tags': [],
        }
        self.c.package_register_post(package)
        status = self.c.last_status
        assert status == 200, status
        # Check package is registered.
        self.c.package_entity_get(pkg_name)
        status = self.c.last_status
        assert status == 200, status
        message = self.c.last_message
        assert message['name'] == pkg_name
        assert message['url'] == 'orig_url'
        assert message['download_url'] == 'orig_download_url'

    def test_package_entity_put(self):
        pkg_name = self.generate_pkg_name()
        # Register new package.
        package = {
            'name': pkg_name,
            'url': 'orig_url',
            'download_url': 'orig_download_url',
            'tags': [],
        }
        self.c.package_register_post(package)
        status = self.c.last_status
        assert status == 200, status
        
        # Check update of existing package.
        package = {
            'name': pkg_name,
            'url': 'new_url',
            'download_url': 'new_download_url',
            'tags': [],
        }
        self.c.package_entity_put(package)
        status = self.c.last_status
        assert status == 200
        # Check package is updated.
        self.c.package_entity_get(pkg_name)
        status = self.c.last_status
        assert status == 200, status
        message = self.c.last_message
        assert message['name'] == pkg_name
        assert message['url'] == 'new_url'
        assert message['download_url'] == 'new_download_url'


    # package entity delete
