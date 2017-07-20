from collections import namedtuple

from nameko.testing.services import entrypoint_waiter, replace_dependencies
from nameko.testing.utils import get_extension
from nameko.standalone.events import event_dispatcher

from croquemort.crawler import CrawlerService
from croquemort.storages import RedisStorage
from croquemort.tools import generate_hash_for

DummyResponse = namedtuple('res',
                           ['url', 'status_code', 'headers', 'history'])


def test_crawling_url(container_factory, rabbit_config, web_container_config):
    crawler_container = container_factory(CrawlerService, web_container_config)
    storage, dispatch_dep = replace_dependencies(crawler_container, 'storage',
                                                 'dispatch')
    crawler_container.start()
    dispatch = event_dispatcher(rabbit_config)
    with entrypoint_waiter(crawler_container, 'check_url'):
        dispatch('http_server', 'url_to_check',
                 ['http://example.org/test_crawling_url', None, None])
    assert storage.store_url.call_count == 1
    assert storage.store_group.call_count == 0
    assert storage.store_metadata.call_count == 1
    # fired 'url_crawled'
    assert dispatch_dep.call_count == 1


def test_crawling_group(
        container_factory, rabbit_config, web_container_config):
    crawler_container = container_factory(CrawlerService, web_container_config)
    storage, dispatch_dep = replace_dependencies(crawler_container, 'storage',
                                                 'dispatch')
    crawler_container.start()
    dispatch = event_dispatcher(rabbit_config)
    with entrypoint_waiter(crawler_container, 'check_url'):
        dispatch('http_server', 'url_to_check',
                 ['http://example.org/test_crawling_group',
                  'datagouvfr', None])
    assert storage.store_url.call_count == 1
    assert storage.store_group.call_count == 1
    assert storage.store_metadata.call_count == 1
    # fired 'url_crawled'
    assert dispatch_dep.call_count == 1


def test_store_redirect_metadata(
        container_factory, rabbit_config, web_container_config):
    res = DummyResponse('http://redirect-done.com', 200, None,
                        [DummyResponse('http://redirecting.com', 301, None,
                         None)])
    crawler_container = container_factory(CrawlerService, web_container_config)
    crawler_container.start()
    storage = get_extension(crawler_container, RedisStorage)
    storage.store_url('http://redirect.com')
    storage.store_metadata('http://redirect.com', res)
    stored = storage.get_url(generate_hash_for('url', 'http://redirect.com'))
    assert stored['redirect-url'] == 'http://redirecting.com'
    assert stored['redirect-status-code'] == '301'
    assert stored['checked-url'] == 'http://redirect.com'
    assert stored['final-url'] == 'http://redirect-done.com'
    assert stored['final-status-code'] == '200'
    assert stored.get('url') is None
    assert stored.get('status') is None


def test_store_no_redirect(
        container_factory, rabbit_config, web_container_config):
    res = DummyResponse('http://no-redirect.com', 200, None, [])
    crawler_container = container_factory(CrawlerService, web_container_config)
    crawler_container.start()
    storage = get_extension(crawler_container, RedisStorage)
    storage.store_url('http://no-redirect.com')
    storage.store_metadata('http://no-redirect.com', res)
    stored = storage.get_url(generate_hash_for('url',
                                               'http://no-redirect.com'))
    assert stored.get('redirect-url') is None
    assert stored.get('redirect-status-code') is None
    assert stored['final-url'] == 'http://no-redirect.com'
    assert stored['final-status-code'] == '200'
    assert stored['checked-url'] == 'http://no-redirect.com'
    assert stored.get('url') is None
    assert stored.get('status') is None
