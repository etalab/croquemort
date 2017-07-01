import pytest
from redis import StrictRedis

from nameko.standalone.rpc import ServiceRpcProxy


def pytest_addoption(parser):
    parser.addoption(
        "--redis-uri", action="store", dest='REDIS_URI',
        default='redis://localhost:6379/0',
        help=("The Redis URI to connect to."))


@pytest.yield_fixture
def container_config(request, rabbit_config):
    """Redis and Rabbit configurations yielding

    Redis teardown is done here, Rabbit teardown is managed in `rabbit_config`.
    """
    config = rabbit_config
    config['REDIS_URI'] = request.config.getoption('REDIS_URI')
    yield config

    # use redis-py API directly to flush the db after each test
    # more elegant to use nameko API to access storage dep? how?
    def redis_teardown():
        client = StrictRedis.from_url(config['REDIS_URI'])
        client.flushdb()
    request.addfinalizer(redis_teardown)


@pytest.fixture()
def web_container_config(container_config, web_config):
    """Merge our two favorites config: container (Rabbit and Redis) and web"""
    return {**web_config, **container_config} # noqa


@pytest.yield_fixture
def rpc_proxy_factory(container_config):
    """ Factory fixture for standalone RPC proxies.
    Proxies are started automatically so they can be used without a ``with``
    statement. All created proxies are stopped at the end of the test, when
    this fixture closes.
    """
    all_proxies = []

    def make_proxy(service_name, **kwargs):
        proxy = ServiceRpcProxy(service_name, container_config, **kwargs)
        all_proxies.append(proxy)
        return proxy.start()

    yield make_proxy

    for proxy in all_proxies:
        proxy.stop()
