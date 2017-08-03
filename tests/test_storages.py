from nameko.testing.utils import get_extension

from croquemort.http import HttpService
from croquemort.storages import RedisStorage


def test_frequencies(container_factory, web_container_config):
    test_container = container_factory(HttpService, web_container_config)
    test_container.start()
    storage = get_extension(test_container, RedisStorage)
    storage.store_group('http://example1.com', 'group1')
    storage.store_group('http://example2.com', 'group2')
    storage.store_frequency('http://example1.com', 'group1', 'hourly')
    storage.store_frequency('http://example2.com', 'group2', 'hourly')
    urls = [u for u in storage.get_frequency_urls('hourly')]
    assert 'http://example1.com' in urls
    assert 'http://example2.com' in urls
    assert len(urls) == 2
