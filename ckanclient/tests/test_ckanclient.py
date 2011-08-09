import exceptions

from nose.tools import assert_raises, assert_equal
from nose.plugins.skip import SkipTest
from pylons import config

from ckan.tests import CkanServerCase

from ckanclient import CkanClient, CkanApiError


config_path = config['__file__']

class TestCkanClient(CkanServerCase):

    @classmethod
    def setup_class(self):
        self.pid = self._start_ckan_server()
        self.test_base_location = 'http://127.0.0.1:5000/api'
        self._wait_for_url(url=self.test_base_location)
        self._recreate_ckan_server_testdata(config_path)
        # this is api key created for tester user by create-test-data in ckan
        test_api_key = 'tester'
        test_api_key2 = 'tester2'
        
        self.c = CkanClient(
            base_location=self.test_base_location,
            api_key=test_api_key,
            is_verbose=True,
        )
        self.c2 = CkanClient(
            base_location=self.test_base_location,
            api_key=test_api_key2,
            is_verbose=True,
        )

    @classmethod
    def teardown_class(self):
        self._stop_ckan_server(self.pid)

    def delete_relationships(self):
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
        assert url == self.test_base_location, url
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

    def test_02_get_api_version(self):
        version = self.c.api_version_get()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert 'version' in body, body
        assert int(version) > 0, version

    def test_03_package_register_get(self):
        self.c.package_register_get()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert 'annakarenina' in body, body
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
        assert_raises(CkanApiError,
                      self.c.package_entity_get,
                      'mycoffeecup')
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
        assert_raises(CkanApiError,
                      self.c.package_entity_get, pkg_name)
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
        assert status == 201, status

        # Check package is registered.
        self.c.package_entity_get(pkg_name)
        status = self.c.last_status
        assert status == 200, status
        message = self.c.last_message
        assert message
        assert 'name' in message, repr(message)
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
        pkg_name_test_07 = self._generate_pkg_name()
        package = {
            'name': pkg_name_test_07,
            'url': 'orig_url',
            'download_url': 'orig_download_url',
            'tags': ['russian'],
        }
        self.c.package_register_post(package)
        status = self.c.last_status
        assert status == 201, status

        # Check update of existing package.
        mytag = 'mytag' + pkg_name_test_07
        package = {
            'name': pkg_name_test_07,
            'url': 'new_url',
            'download_url': 'new_download_url',
            'tags': ['russian', 'tolstoy', mytag],
            'extras': {'genre':'thriller', 'format':'ebook'},
        }
        self.c.package_entity_put(package)
        status = self.c.last_status
        assert status == 200

        # Check package is updated.
        self.c.package_entity_get(pkg_name_test_07)
        status = self.c.last_status
        assert status == 200, status
        message = self.c.last_message
        name = message['name']
        assert name == pkg_name_test_07
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
        # create a package to be deleted
        pkg_name = self._generate_pkg_name()
        self.c.package_register_post({'name': pkg_name})
        status = self.c.last_status
        assert status == 201, status        

        # check it is readable
        self.c.package_entity_get(pkg_name)
        assert self.c.last_status == 200, self.c.last_status

        # delete it
        self.c.package_entity_delete(pkg_name)

        # see it is not readable by another user
        assert_raises(CkanApiError,
                      self.c2.package_entity_get, pkg_name)
        assert self.c2.last_status == 403, self.c.last_status

        # see it is still readable by the author (therefore pkg admin)
        self.c.package_entity_get(pkg_name)
        assert self.c.last_status == 200, self.c.last_status

    def test_09_tag_register_get(self):
        self.c.tag_register_get()
        status = self.c.last_status
        assert status == 200
        body = self.c.last_body
        assert 'russian' in body
        assert type(self.c.last_message) == list
        assert 'russian' in self.c.last_message

    def test_10_pkg_search_basic(self):
        res = self.c.package_search('Novel')
        status = self.c.last_status
        assert status == 200, status
        assert_equal(list(res['results']), [u'annakarenina'])
        assert_equal(res['count'], 1)

    def test_10_pkg_search_paged(self):
        res = self.c.package_search('russian', search_options={'limit': 1})
        status = self.c.last_status
        assert status == 200, status
        all_results = list(res['results'])
        assert set(all_results) >= set([u'annakarenina', u'warandpeace']), all_results
        assert res['count'] >= 2, '%r %r' % (res, all_results)

    def test_10_pkg_search_options(self):
        res = self.c.package_search(None, search_options={'groups': 'roger'})
        status = self.c.last_status
        assert status == 200, status
        assert_equal(list(res['results']), [u'annakarenina'])
        assert_equal(res['count'], 1)

    def test_10_pkg_search_options_all_fields(self):
        res = self.c.package_search(None, search_options={'groups': 'roger',
                                                          'all_fields': True})
        status = self.c.last_status
        assert status == 200, status
        assert_equal(res['count'], 1)
        assert_equal(list(res['results'])[0]['name'], u'annakarenina')

    def test_11_package_relationship_post(self):
        res = self.c.package_relationship_register_get('annakarenina')
        assert self.c.last_status == 200, self.c.last_status
        assert not self.c.last_message, self.c.last_body

        # create relationship
        res = self.c.package_relationship_entity_post('annakarenina', 'child_of', 'warandpeace', 'some comment')
        try:
            assert self.c.last_status == 201, self.c.last_status
        finally:
            self.delete_relationships()
        
    def test_12_package_relationship_get(self):
        # create relationship
        res = self.c.package_relationship_entity_post('annakarenina', 'child_of', 'warandpeace', 'some comment')
        
        # read relationship
        try:
            res = self.c.package_relationship_register_get('annakarenina')
            assert self.c.last_status == 200, self.c.last_status
            rels = self.c.last_message
            assert len(rels) == 1, rels
            assert rels[0]['subject'] == 'annakarenina', rels[0]
            assert rels[0]['object'] == 'warandpeace', rels[0]
            assert rels[0]['type'] == 'child_of', rels[0]
            assert rels[0]['comment'] == 'some comment', rels[0]
        finally:
            self.delete_relationships()

    def test_13_package_relationship_put(self):
        # create relationship
        res = self.c.package_relationship_entity_post('annakarenina', 'child_of', 'warandpeace', 'some comment')
        # update relationship
        try:
            res = self.c.package_relationship_entity_put('annakarenina', 'child_of', 'warandpeace', 'new comment')
            assert self.c.last_status == 200, self.c.last_status

            # read relationship
            res = self.c.package_relationship_register_get('annakarenina')
            assert self.c.last_status == 200, self.c.last_status
            rels = self.c.last_message
            assert len(rels) == 1, rels
            assert rels[0]['comment'] == 'new comment', rels[0]
        finally:
            self.delete_relationships()

    def test_14_package_relationship_delete(self):
        # create relationship
        res = self.c.package_relationship_entity_post('annakarenina', 'child_of', 'warandpeace', 'some comment')
        try:
            self.c.package_relationship_entity_delete('annakarenina',
                                                      'child_of', 'warandpeace')

            # read relationship gives 404
            assert_raises(CkanApiError,
                          self.c.package_relationship_register_get,
                          'annakarenina', 'child_of', 'warandpeace')
            assert self.c.last_status == 404, self.c.last_status

            # and register of relationships is blank
            res = self.c.package_relationship_register_get('annakarenina', 'relationships', 'warandpeace')
            assert self.c.last_status == 200, self.c.last_status
            assert not res, res
        finally:
            self.delete_relationships()

    def test_15_package_edit_form_get(self):
        try:
            import ckanext.dgu
        except exceptions.ImportError, e:
            raise SkipTest('Need dgu_form_api plugin (from ckanext-dgu) installed to test form api client.')
        if 'dgu_form_api' not in config.get('ckan.plugins', ''):
            raise SkipTest('Need dgu_form_api plugin (from ckanext-dgu) enabled to test form api client.')
            
        res = self.c.package_edit_form_get('annakarenina')
        assert self.c.last_status == 200, self.c.last_status
        assert res, res
        
    def test_16_group_get(self):
        groups = self.c.group_register_get()
        assert 'david' in groups, groups
        assert 'roger' in groups
        david = self.c.group_entity_get('david')
        for expected_key in ('name', 'id', 'title', 'created', 'description'):
            assert expected_key in david, david
        assert set(david['packages']) == set((u'annakarenina', u'warandpeace')), david
        roger = self.c.group_entity_get('roger')
        assert roger['packages'] == [u'annakarenina'], roger
