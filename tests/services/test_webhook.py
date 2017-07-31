import requests
import requests_mock

from nameko.standalone.events import event_dispatcher
from nameko.testing.services import entrypoint_waiter, replace_dependencies

from croquemort.webhook import WebhookService


def filter_requests(url, requests_l):
    return [r for r in requests_l if url in r.url]


@requests_mock.Mocker(kw='rmock', real_http=True)
def test_webhook_valid_call(
        web_container_config, container_factory, rmock=None):
    test_url = 'http://example.org'
    test_cb_url = 'http://example.org/cb'
    container = container_factory(WebhookService, web_container_config)
    storage = replace_dependencies(container, 'storage')
    storage.get_webhooks_for_url = lambda url: [test_cb_url]
    container.start()
    dispatch = event_dispatcher(web_container_config)
    rmock.post(test_cb_url, text='xxx')
    with entrypoint_waiter(container, 'send_response'):
        dispatch('url_crawler', 'url_crawled', {'checked-url': test_url})
    requests_l = filter_requests(test_cb_url, rmock.request_history)
    assert len(requests_l) == 1
    request = requests_l[0]
    assert request.method == 'POST'
    assert request.url == test_cb_url
    assert request.json() == {'data': {'checked-url': test_url}}


@requests_mock.Mocker(kw='rmock', real_http=True)
def test_webhook_retry(
        web_container_config, container_factory, rmock=None):
    test_url = 'http://example.org'
    test_cb_url = 'http://example.org/cb'
    web_container_config['WEBHOOK_DELAY_INTERVAL'] = 1
    web_container_config['WEBHOOK_BACKOFF_FACTOR'] = 1
    container = container_factory(WebhookService, web_container_config)
    storage = replace_dependencies(container, 'storage')
    storage.get_webhooks_for_url = lambda url: [test_cb_url]
    container.start()
    dispatch = event_dispatcher(web_container_config)
    # 1 failed response and then a valid one
    rmock.post(test_cb_url, [{'status_code': 404}, {'status_code': 200}])
    with entrypoint_waiter(container, 'send_response'):
        dispatch('url_crawler', 'url_crawled', {'checked-url': test_url})
    requests_l = filter_requests(test_cb_url, rmock.request_history)
    assert len(requests_l) == 2
    request = requests_l[-1]
    assert request.method == 'POST'
    assert request.url == test_cb_url
    assert request.json() == {'data': {'checked-url': test_url}}


@requests_mock.Mocker(kw='rmock', real_http=True)
def test_webhook_timeout_retry(
        web_container_config, container_factory, rmock=None):
    test_url = 'http://example.org'
    test_cb_url = 'http://example.org/cb'
    web_container_config['WEBHOOK_DELAY_INTERVAL'] = 1
    web_container_config['WEBHOOK_BACKOFF_FACTOR'] = 1
    container = container_factory(WebhookService, web_container_config)
    storage = replace_dependencies(container, 'storage')
    storage.get_webhooks_for_url = lambda url: [test_cb_url]
    container.start()
    dispatch = event_dispatcher(web_container_config)
    # 1 failed response and then a valid one
    rmock.post(test_cb_url, [{'exc': requests.exceptions.ConnectTimeout},
                             {'status_code': 200}])
    with entrypoint_waiter(container, 'send_response'):
        dispatch('url_crawler', 'url_crawled', {'checked-url': test_url})
    requests_l = filter_requests(test_cb_url, rmock.request_history)
    assert len(requests_l) == 2
    request = requests_l[-1]
    assert request.method == 'POST'
    assert request.url == test_cb_url
    assert request.json() == {'data': {'checked-url': test_url}}
