import json
from mock import ANY

from nameko.testing.services import replace_dependencies

from croquemort.http import HttpService


def test_retrieve_url(container_factory, web_session, web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    storage = replace_dependencies(http_container, 'storage')
    storage.get_url = lambda url_hash: {'url': url_hash}
    http_container.start()
    rv = web_session.get('/url', data=json.dumps({
        'url': 'http://example.org/test_retrieve_url'
    }))
    assert rv.json()['url'] == 'u:9c01c218'
    assert 'group' not in rv.json()


def test_cache_report(container_factory, web_session, web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    storage = replace_dependencies(http_container, 'storage')
    storage.set_cache.return_value = None
    storage.get_cache.return_value = None
    storage.expire_cache.return_value = None
    http_container.start()

    rv = web_session.get('/')
    cache_duration = 60 * 60 * 2  # Equals 2 hours.
    default_key = 'cache-display_report-'
    assert rv.text.startswith('<!doctype html>')
    storage.get_cache.assert_called_once_with(default_key)
    storage.set_cache.assert_called_once_with(default_key, ANY)  # HTML.
    storage.expire_cache.assert_called_once_with(default_key, cache_duration)


def test_retrieve_url_with_group(
        container_factory, web_session, web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    storage = replace_dependencies(http_container, 'storage')
    storage.get_url = lambda url_hash: {
        'url': url_hash,
        'group': 'datagouvfr'
    }
    http_container.start()
    rv = web_session.get('/url', data=json.dumps({
        'url': 'http://example.org/test_retrieve_url_with_group'
    }))
    assert rv.json()['url'] == 'u:462bd375'
    assert rv.json()['group'] == 'datagouvfr'


def test_retrieve_group(container_factory, web_session, web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    storage = replace_dependencies(http_container, 'storage')
    storage.get_group = lambda group_hash: {
        'url': group_hash,
        'name': 'datagouvfr',
        'url_hash': 'url'
    }
    storage.get_url = lambda url_hash: {'url': url_hash}
    http_container.start()
    rv = web_session.get('/group', data=json.dumps({
        'group': 'datagouvfr'
    }))
    result = rv.json()
    assert result['name'] == 'datagouvfr'
    assert 'url_hash' in result['urls'][0].values()


def test_retrieve_group_filtered(
        container_factory, web_session, web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    storage = replace_dependencies(http_container, 'storage')
    storage.get_group = lambda group_hash: {
        'url': group_hash,
        'name': 'datagouvfr',
        'url_hash1': 'url1',
        'url_hash2': 'url1',
    }

    def get_url(url_hash):
        result = {'url': url_hash}
        if url_hash == 'url_hash1':
            result['metadata'] = 'meta'
        return result

    storage.get_url = get_url
    http_container.start()
    rv = web_session.get('/group', data=json.dumps({
        'group': 'datagouvfr',
        'filter_metadata': 'meta'
    }))
    result = rv.json()
    assert result['name'] == 'datagouvfr'
    assert 'url_hash1' in result['urls'][0].values()
    assert 'url_hash2' not in result['urls'][0].values()


def test_retrieve_group_excluded(
        container_factory, web_session, web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    storage = replace_dependencies(http_container, 'storage')
    storage.get_group = lambda group_hash: {
        'url': group_hash,
        'name': 'datagouvfr',
        'url_hash1': 'url1',
        'url_hash2': 'url1',
    }

    def get_url(url_hash):
        result = {'url': url_hash}
        if url_hash == 'url_hash1':
            result['metadata'] = 'meta'
        return result

    storage.get_url = get_url
    http_container.start()
    rv = web_session.get('/group', data=json.dumps({
        'group': 'datagouvfr',
        'exclude_metadata': 'meta'
    }))
    result = rv.json()
    assert result['name'] == 'datagouvfr'
    assert 'url_hash1' not in result['urls'][0].values()
    assert 'url_hash2' in result['urls'][0].values()


def test_retrieve_group_excluded_empty(
        container_factory, web_session, web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    storage = replace_dependencies(http_container, 'storage')
    storage.get_group = lambda group_hash: {
        'url': group_hash,
        'name': 'datagouvfr',
        'url_hash1': 'url1',
        'url_hash2': 'url1',
    }

    def get_url(url_hash):
        result = {'url': url_hash}
        if url_hash == 'url_hash1':
            result['metadata'] = ''
        return result

    storage.get_url = get_url
    http_container.start()
    rv = web_session.get('/group', data=json.dumps({
        'group': 'datagouvfr',
        'exclude_metadata': ''
    }))
    result = rv.json()
    assert result['name'] == 'datagouvfr'
    assert 'url_hash1' not in result['urls'][0].values()
    assert 'url_hash2' in result['urls'][0].values()


def test_checking_one(container_factory, web_session, web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    dispatch = replace_dependencies(http_container, 'dispatch')
    http_container.start()
    rv = web_session.post('/check/one', data=json.dumps({
        'url': 'http://example.org/test_checking_one'
    }))
    assert rv.json()['url-hash'] == 'u:a55f9fb5'
    assert dispatch.call_count == 1


def test_checking_one_webhook(container_factory, web_session,
                              web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    storage = replace_dependencies(http_container, 'storage')
    http_container.start()
    web_session.post('/check/one', data=json.dumps({
        'url': 'http://example.org/test_checking_one',
        'callback_url': 'http://example.org/cb'
    }))
    assert storage.store_webhook.call_count == 1


def test_checking_one_webhook_wrong_url(container_factory, web_session,
                                        web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    storage = replace_dependencies(http_container, 'storage')
    http_container.start()
    web_session.post('/check/one', data=json.dumps({
        'url': 'http://example.org/test_checking_one',
        'callback_url': 'not-an-url'
    }))
    assert storage.store_webhook.call_count == 0


def test_checking_many(container_factory, web_session, web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    dispatch = replace_dependencies(http_container, 'dispatch')
    http_container.start()
    rv = web_session.post('/check/many', data=json.dumps({
        'urls': [
            'http://example.org/test_checking_many',
            'http://example.com/test_checking_many'
        ],
        'group': 'datagouvfr'
    }))
    assert rv.json()['group-hash'] == 'g:efcf3897'
    assert dispatch.call_count == 2


def test_checking_many_webhook(container_factory, web_session,
                               web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    storage = replace_dependencies(http_container, 'storage')
    http_container.start()
    web_session.post('/check/many', data=json.dumps({
        'urls': [
            'http://example.org/test_checking_many',
            'http://example.com/test_checking_many'
        ],
        'callback_url': 'http://example.org/cb',
        'group': 'datagouvfr'
    }))
    assert storage.store_webhook.call_count == 2


def test_fetching(container_factory, rpc_proxy_factory, web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    http_server = rpc_proxy_factory('http_server')
    dispatch = replace_dependencies(http_container, 'dispatch')
    http_container.start()
    http_server.fetch('http://example.org/test_fetching')
    assert dispatch.call_count == 1


def test_fetching_w_webhook(container_factory, rpc_proxy_factory,
                            web_container_config):
    http_container = container_factory(HttpService, web_container_config)
    http_server = rpc_proxy_factory('http_server')
    storage = replace_dependencies(http_container, 'storage')
    http_container.start()
    http_server.fetch('http://example.org/test_fetching',
                      callback_url='http://example.org/cb')
    assert storage.store_webhook.call_count == 1
