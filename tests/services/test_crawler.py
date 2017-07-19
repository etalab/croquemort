from nameko.testing.services import entrypoint_waiter, replace_dependencies
from nameko.standalone.events import event_dispatcher

from croquemort.crawler import CrawlerService


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
