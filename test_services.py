import pytest

from nameko.runners import ServiceRunner
from nameko.standalone.rpc import ServiceRpcProxy
from nameko.standalone.events import event_dispatcher
from nameko.testing.utils import get_container
from nameko.testing.services import entrypoint_waiter, replace_dependencies

from crawler import CrawlerService
from http import HttpService


@pytest.yield_fixture
def runner_factory(rabbit_config):

    all_runners = []

    def make_runner(*service_classes):
        runner = ServiceRunner(rabbit_config)
        for service_cls in service_classes:
            runner.add_service(service_cls)
        all_runners.append(runner)
        return runner

    yield make_runner

    for r in all_runners:
        try:
            r.stop()
        except:
            pass


@pytest.yield_fixture
def rpc_proxy_factory(rabbit_config):
    """ Factory fixture for standalone RPC proxies.

    Proxies are started automatically so they can be used without a ``with``
    statement. All created proxies are stopped at the end of the test, when
    this fixture closes.
    """
    all_proxies = []

    def make_proxy(service_name, **kwargs):
        proxy = ServiceRpcProxy(service_name, rabbit_config, **kwargs)
        all_proxies.append(proxy)
        return proxy.start()

    yield make_proxy

    for proxy in all_proxies:
        proxy.stop()


def test_http(runner_factory, rpc_proxy_factory):
    runner = runner_factory(HttpService)
    http_server = rpc_proxy_factory('http_server')
    http_container = get_container(runner, HttpService)
    dispatch = replace_dependencies(http_container, 'dispatch')
    runner.start()
    http_server.fetch('http://example.org')
    assert dispatch.call_count == 1


def test_crawler(runner_factory, rpc_proxy_factory):
    runner = runner_factory(CrawlerService)
    crawler_container = get_container(runner, CrawlerService)
    storage = replace_dependencies(crawler_container, 'storage')
    runner.start()
    config = {'AMQP_URI': 'amqp://guest:guest@localhost:5672/nameko_test'}
    dispatch = event_dispatcher(config)
    with entrypoint_waiter(crawler_container, 'check_url'):
        dispatch('http_server', 'url_to_check', ['http://example.org', None])
    assert storage.store_url.call_count == 1
    assert storage.store_group.call_count == 0
    assert storage.store_metadata.call_count == 1
