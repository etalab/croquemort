import eventlet
eventlet.monkey_patch()  # noqa (code before rest of imports)

import itertools
import logging
import socket
import sys

from kombu import pools
from mock import patch
import pytest

from nameko.containers import ServiceContainer
from nameko.standalone.rpc import ServiceRpcProxy
from nameko.testing import rabbit
from nameko.testing.utils import (
    reset_rabbit_vhost, reset_rabbit_connections,
    get_rabbit_connections, get_rabbit_config)
from nameko.testing.websocket import make_virtual_socket
from nameko.web.server import parse_address


def pytest_addoption(parser):
    parser.addoption(
        "--redis-uri", action="store", dest='REDIS_URI',
        default='redis://localhost:6379/0',
        help=("The Redis URI to connect to."))


def pytest_configure(config):
    if config.option.blocking_detection:
        from eventlet import debug
        debug.hub_blocking_detection(True)

    log_level = config.getoption('log_level')
    if log_level is not None:
        log_level = getattr(logging, log_level)
        logging.basicConfig(level=log_level, stream=sys.stderr)


@pytest.fixture(scope='session')
def rabbit_manager(request):
    config = request.config
    return rabbit.Client(config.getoption('RABBIT_CTL_URI'))


@pytest.yield_fixture()
def rabbit_config(request, rabbit_manager):
    amqp_uri = request.config.getoption('AMQP_URI')

    conf = get_rabbit_config(amqp_uri)

    reset_rabbit_connections(conf['vhost'], rabbit_manager)
    reset_rabbit_vhost(conf['vhost'], conf['username'], rabbit_manager)

    yield conf

    pools.reset()  # close connections in pools

    # raise a runtime error if the test leaves any connections lying around
    connections = get_rabbit_connections(conf['vhost'], rabbit_manager)
    if connections:
        count = len(connections)
        raise RuntimeError("{} rabbit connection(s) left open.".format(count))


@pytest.yield_fixture
def container_config(request, rabbit_config):
    config = rabbit_config
    config['REDIS_URI'] = request.config.getoption('REDIS_URI')
    yield config


@pytest.yield_fixture
def container_factory(container_config):
    all_containers = []

    def make_container(service_cls, config, worker_ctx_cls=None):
        container = ServiceContainer(service_cls, config, worker_ctx_cls)
        all_containers.append(container)
        return container

    yield make_container

    for c in all_containers:
        try:
            c.stop()
        except:
            pass


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


@pytest.yield_fixture
def predictable_call_ids(request):
    with patch('nameko.containers.new_call_id', autospec=True) as get_id:
        get_id.side_effect = (str(i) for i in itertools.count())
        yield get_id


@pytest.yield_fixture()
def web_config(container_config):
    # find a port that's likely to be free
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()

    cfg = container_config
    cfg['WEB_SERVER_ADDRESS'] = str(port)
    yield cfg


@pytest.fixture()
def web_config_port(web_config):
    return parse_address(web_config['WEB_SERVER_ADDRESS']).port


@pytest.yield_fixture()
def web_session(web_config_port):
    from requests import Session
    from werkzeug.urls import url_join

    class WebSession(Session):
        def request(self, method, url, *args, **kwargs):
            url = url_join('http://127.0.0.1:%d/' % web_config_port, url)
            return Session.request(self, method, url, *args, **kwargs)

    sess = WebSession()
    with sess:
        yield sess


@pytest.yield_fixture()
def websocket(web_config_port):
    active_sockets = []

    def socket_creator():
        ws_app, wait_for_sock = make_virtual_socket(
            '127.0.0.1', web_config_port)
        gr = eventlet.spawn(ws_app.run_forever)
        active_sockets.append((gr, ws_app))
        return wait_for_sock()

    try:
        yield socket_creator
    finally:
        for gr, ws_app in active_sockets:
            try:
                ws_app.close()
            except Exception:
                pass
            gr.kill()
