from ckanclient import CkanClient

# Todo: Discovery of local api-key for the okfntest:okfntest test user.

class TestCkanClient(object):

    # To run tests:

    #  1. Run a test server in another shell
    #      $ paster serve development.ini
    #  2. On the test server run:
    #      $ paster db clean && paster db init && paster create-test-data
    test_base_location = 'http://127.0.0.1:5000/api'
    # this is api key created for tester user by create-test-data in ckan
    test_api_key = 'tester'
    #  3. Run these tests with nose:
    #      $ nosetests ckanclient/tests

    def setup(self):
        self.c = CkanClient(
            base_location=self.test_base_location,
            api_key=self.test_api_key,
            is_verbose=True,
        )
        self.pkg_name_test_07 = self._generate_pkg_name()

    def teardown(self):
        # delete relationships
        res = self.c.package_relationship_register_get('annakarenina')
        if self.c.last_status == 200:
            if self.c.last_message:
                for rel_dict in self.c.last_message:
                    self.c.package_relationship_entity_delete( \
                        rel_dict['subject'],
                        rel_dict['type'],
                        rel_dict['object'])
        

    def test_01_get_locations(self):
        rest_base = self.test_base_location + '/rest'
        search_base = self.test_base_location + '/search'
        url = self.c.get_location('Base')
        assert url == self.test_base_location + '/', url
        url = self.c.get_location('Package Register')
        assert url == rest_base + '/package'
        url = self.c.get_location('Package Entity', 'myname')
        assert url == rest_base + '/package/myname'
        url = self.c.get_location('Package Entity', 'myname',
                                  'relationships')
        assert url == rest_base + '/package/myname/relationships'
        url = self.c.get_location('Package Entity', 'myname',
                                  'relationships', 'name2')
        assert url == rest_base + '/package/myname/relationships/name2'
        url = self.c.get_location('Package Entity', 'myname',
                                  'child_of', 'name2')
        assert url == rest_base + '/package/myname/child_of/name2'
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

    def test_02_open_base_location(self):
        assert self.c.base_location == self.test_base_location
        self.c.open_base_location()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert '<h2>API</h2>' in body, body
        # Not sure why this doesn't work anymore
        # header = self.c.last_headers.get('Connection')
        # assert header == 'close', self.c.last_headers

    def test_03_package_register_get(self):
        self.c.package_register_get()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert 'annakarenina' in body
        assert type(self.c.last_message) == list
        assert 'annakarenina' in self.c.last_message

    def test_04_package_entity_get(self):
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

    def test_05_package_entity_get_404(self):
        # Check unregistered entity is not found.
        self.c.package_entity_get('mycoffeecup')
        status = self.c.last_status
        assert status == 404, status

    @classmethod
    def _generate_pkg_name(self):
        pkg_name = 'ckanclienttest'
        import time
        timestr = str(time.time()).replace('.', '')
        pkg_name += timestr
        return pkg_name

    def test_06_package_register_post(self):
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
        # order out is not guaranteed
        assert set(tags) == set(['newtag', 'russian']), tags
        extras = message['extras']
        assert extras == package['extras']
        

    def test_07_package_entity_put(self):
        # Register new package.
        package = {
            'name': self.pkg_name_test_07,
            'url': 'orig_url',
            'download_url': 'orig_download_url',
            'tags': ['russian'],
        }
        self.c.package_register_post(package)
        status = self.c.last_status
        assert status == 200, status
        
        # Check update of existing package.
        mytag = 'mytag' + self.pkg_name_test_07
        package = {
            'name': self.pkg_name_test_07,
            'url': 'new_url',
            'download_url': 'new_download_url',
            'tags': ['russian', 'tolstoy', mytag],
            'extras': {'genre':'thriller', 'format':'ebook'},
        }
        self.c.package_entity_put(package)
        status = self.c.last_status
        assert status == 200

        # Check package is updated.
        self.c.package_entity_get(self.pkg_name_test_07)
        status = self.c.last_status
        assert status == 200, status
        message = self.c.last_message
        name = message['name']
        assert name == self.pkg_name_test_07
        url = message['url']
        assert url == 'new_url'
        download_url = message['download_url']
        assert download_url == 'new_download_url'
        tags = message['tags']
        # order out is not guaranteed
        assert set(tags) == set(['russian', 'tolstoy', mytag]), tags
        extras = message['extras']
        assert extras == package['extras']

    def test_08_package_entity_delete(self):
        # follows on from test_07
        self.test_07_package_entity_put()
        assert self.pkg_name_test_07
        # check it is still there
        self.c.package_entity_get(self.pkg_name_test_07)
        assert self.c.last_status == 200, self.c.last_status

        self.c.package_entity_delete(self.pkg_name_test_07)

        # see it is not readable
        self.c.package_entity_get(self.pkg_name_test_07)
        assert self.c.last_status == 403, self.c.last_status

    def test_09_tag_register_get(self):
        self.c.tag_register_get()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert 'russian' in body
        assert type(self.c.last_message) == list
        assert 'russian' in self.c.last_message

    def test_10_pkg_search_basic(self):
        res = self.c.package_search('annakarenina')
        status = self.c.last_status
        assert status == 200, status
        assert res['count'] == 1, res
        assert res['results'] == [u'annakarenina']

    def test_11_package_relationship_post(self):
        res = self.c.package_relationship_register_get('annakarenina')
        assert self.c.last_status == 200, self.c.last_status
        assert not self.c.last_message, self.c.last_body

        # create relationship
        res = self.c.package_relationship_entity_post('annakarenina', 'child_of', 'warandpeace', 'some comment')
        assert self.c.last_status == 200, self.c.last_status
        
    def test_12_package_relationship_get(self):
        # check no existing relationships
        # follows on from test_11
        self.test_11_package_relationship_post()
        # read relationship
        res = self.c.package_relationship_register_get('annakarenina')
        assert self.c.last_status == 200, self.c.last_status
        rels = self.c.last_message
        assert len(rels) == 1, rels
        assert rels[0]['subject'] == 'annakarenina', rels[0]
        assert rels[0]['object'] == 'warandpeace', rels[0]
        assert rels[0]['type'] == 'child_of', rels[0]
        assert rels[0]['comment'] == 'some comment', rels[0]

    def test_13_package_relationship_put(self):
        # follows on from test_12
        self.test_12_package_relationship_get()
        # update relationship
        res = self.c.package_relationship_entity_put('annakarenina', 'child_of', 'warandpeace', 'new comment')
        assert self.c.last_status == 200, self.c.last_status

        # read relationship
        res = self.c.package_relationship_register_get('annakarenina')
        assert self.c.last_status == 200, self.c.last_status
        rels = self.c.last_message
        assert len(rels) == 1, rels
        assert rels[0]['comment'] == 'new comment', rels[0]

    def test_14_package_relationship_delete(self):
        # follows on from test_11/12
        self.c.package_relationship_entity_delete('annakarenina',
                                                  'child_of', 'warandpeace')

        # read relationship gives 404
        res = self.c.package_relationship_register_get('annakarenina', 'child_of', 'warandpeace')
        assert self.c.last_status == 404, self.c.last_status

        # and register of relationships is blank
        res = self.c.package_relationship_register_get('annakarenina', 'relationships', 'warandpeace')
        assert self.c.last_status == 200, self.c.last_status
        assert not res, res
