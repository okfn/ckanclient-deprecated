import ckanclient.datastore
import json

class TestDataStore:
    base_url = 'http://localhost:9200/datastore-client-test'

    def test_url_parse(self):
        url = 'http://abc@localhost:8088/api/data/75328a3a-e566-4993-9115-6e915ed7362c'
        client = ckanclient.datastore.DataStoreClient(url)
        assert client.netloc == 'localhost:8088'
        assert client.authorization == 'abc'
        assert client.es_type_name == '75328a3a-e566-4993-9115-6e915ed7362c' 

        url = 'http://abc@localhost:8088/dataset/xyz/resource/75328a3a-e566-4993-9115-6e915ed7362c'
        client = ckanclient.datastore.DataStoreClient(url)
        assert client.netloc == 'localhost:8088'
        assert client.authorization == 'abc'
        assert client.url == 'http://localhost:8088/api/data/75328a3a-e566-4993-9115-6e915ed7362c' 
        assert client.es_type_name == '75328a3a-e566-4993-9115-6e915ed7362c' 

    def test_delete(self):
        url = self.base_url + '/delete-test'
        client = ckanclient.datastore.DataStoreClient(url)
        out = client.delete()
        data = json.loads(out)
        assert data['ok'] == True, data

    def test_upload(self):
        url = self.base_url + '/update-test'
        from StringIO import StringIO
        data = StringIO("""[{"a": 1, "b": 2, "c": 3}]""")
        client = ckanclient.datastore.DataStoreClient(url)
        client.upload(data, filetype='json')

    query_data = [
            {"a": 'john', "b": 2, "c": "UK"},
            {"a": 'jane', "b": 5, "c": "UK"},
            {"a": 'john', "b": 7, "c": "DE"}
        ]

    def test_query(self):
        url = self.base_url + '/query-test'
        client = ckanclient.datastore.DataStoreClient(url)
        client.delete()
        client.upsert(self.query_data, refresh=True)
        query = {
            'query': { 
                'match_all': {}
            }
        }
        out = client.query(query)
        import pprint
        assert out['hits']['total'] == 3, pprint.pprint(out)

        query = {
            'query': {
                'constant_score': { 
                    'filter': {
                        'term': {
                            # must be lower-case!
                            'c': 'uk'
                        }
                    }
                }
            }
        }
        out = client.query(query)
        assert out['hits']['total'] == 2, pprint.pprint(out)

        query = {
            'query': {
                "constant_score" : {
                    "filter" : {
                        "range" : {
                            "b" : { 
                                "from" : 4, 
                                "to" : "8"
                            }
                        }
                    }
                }
            }
        }
        out = client.query(query)
        assert out['hits']['total'] == 2, pprint.pprint(out)

        query = {
            'query': {
                "range" : {
                    "b" : { 
                        "from" : 4, 
                        "to" : "8"
                    }
                }
            }
        }
        out = client.query(query)
        assert out['hits']['total'] == 2, pprint.pprint(out)

        query = {
            "query": {
                "filtered": {
                    "query": {
                        "match_all": {}
                    },
                    "filter": {
                        "and": [
                            {
                                "range" : {
                                    "b" : { 
                                        "from" : 4, 
                                        "to" : "8"
                                    }
                                },
                            },
                            {
                                "term": {
                                    "a": "john"
                                }
                            }
                        ]
                    }
                }
            }
        }
        out = client.query(query)
        assert out['hits']['total'] == 1, pprint.pprint(out)

    def test_query_facet(self):
        url = self.base_url + '/query-test'
        client = ckanclient.datastore.DataStoreClient(url)
        client.delete()
        client.upsert(self.query_data, refresh=True)
        query = {
            'query': { 
                'match_all': {}
            }
        }
        out = client.query(query)
        import pprint
        assert out['hits']['total'] == 3, pprint.pprint(out)

    def test_mapping(self):
        url = self.base_url + '/mapping-test'
        client = ckanclient.datastore.DataStoreClient(url)
        client.delete()
        mapping = {
            'properties': {
                'url': {
                    'type': 'string'
                }
            }
        }
        client.mapping_update(mapping)
        out = client.mapping()
        url = out['mapping-test']['properties']['url']
        assert url
        assert url['type'] == 'string', url



