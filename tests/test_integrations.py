from nameko.standalone.events import event_dispatcher
from nameko.testing.services import entrypoint_waiter, replace_dependencies
from nameko.testing.utils import get_container

from croquemort.crawler import CrawlerService
from croquemort.webhook import WebhookService


def test_crawler_triggers_webhook(runner_factory, web_container_config):
    """Is crawler_container dispatching to webhook_container?"""
    runner = runner_factory(web_container_config, CrawlerService,
                            WebhookService)
                            webhook_container = get_container(runner, WebhookService)
                            storage_w = replace_dependencies(webhook_container, 'storage')
                            dispatch = event_dispatcher(web_container_config)
                            runner.start()
                            with entrypoint_waiter(webhook_container, 'send_response'):
                                dispatch('http_server', 'url_to_check',
                                         ['http://example.org/test_crawling_group',
                                          'datagouvfr', None])
                            assert storage_w.get_webhooks_for_url.call_count == 1

# TODO use config file for KNOWN_HEAD_OFFENDER_DOMAINS (v2)
# TODO use request mock to check HEAD is not called (v2)
def test_crawling_head_offender_url(runner_factory, rpc_proxy_factory):
    runner = runner_factory(CrawlerService)
    crawler_container = get_container(runner, CrawlerService)
    storage = replace_dependencies(crawler_container, 'storage')
    runner.start()
    config = {'AMQP_URI': 'amqp://guest:guest@localhost:5672/nameko_test'}
    dispatch = event_dispatcher(config)
    with entrypoint_waiter(crawler_container, 'check_url'):
        dispatch('http_server', 'url_to_check',
                 ['http://www.bnf.fr/test_crawling_url', None, None])
    assert storage.store_url.call_count == 1
    assert storage.store_group.call_count == 0
    assert storage.store_metadata.call_count == 1
