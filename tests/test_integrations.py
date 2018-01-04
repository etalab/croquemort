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
