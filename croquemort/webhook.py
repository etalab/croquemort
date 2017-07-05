import logbook
import requests

from nameko.dependency_providers import Config
from nameko.events import event_handler
from nameko.utils.retry import retry

from .logger import LoggingDependency
from .storages import RedisStorage

log = logbook.debug

# See http://docs.python-requests.org/en/latest/user/advanced/#timeouts
# We are waiting 3 sec for the connexion and 9 for the response.
TIMEOUT = (3.1, 9.1)

DELAY_INTERVAL = 10  # in seconds
NB_RETRY = 5
# increase the retry delay by this factor at each try
BACKOFF_FACTOR = 2


class WebhookUnreachableException(Exception):

    def __init__(self, message, url, status, original_exception=None):
        super().__init__(message)
        self.url = url
        self.status = status
        self.original_exception = original_exception


class WebhookService(object):
    name = 'webhook_dispatcher'
    storage = RedisStorage()
    logger = LoggingDependency()
    config = Config()

    def _send(self, url, metadata):
        """POST metadata to url"""
        try:
            response = requests.post(url, json={'data': metadata},
                                     timeout=TIMEOUT)
        except (requests.Timeout, requests.RequestException) as e:
            raise WebhookUnreachableException('Unreachable', url, 503,
                                              original_exception=e)
        if response.status_code < 200 or response.status_code >= 400:
            raise WebhookUnreachableException('Unreachable', url,
                                              response.status_code)
        log('Successfully called webhook {url}'.format(url=url))

    @event_handler('url_crawler', 'url_crawled')
    def send_response(self, metadata):
        """Call a webhook with checked url results"""
        url = metadata.get('url')
        callback_urls = self.storage.get_webhooks_for_url(url)
        if not callback_urls:
            return
        for callback_url in callback_urls:
            log(('Calling webhook url {callback_url} for checked url {url}'
                 .format(callback_url=callback_url, url=url)))
            try:
                send = retry(
                    self._send,
                    for_exceptions=WebhookUnreachableException,
                    max_attempts=self.config.get('WEBHOOK_NB_RETRY', NB_RETRY),
                    delay=self.config.get('WEBHOOK_DELAY_INTERVAL',
                                          DELAY_INTERVAL),
                    backoff=self.config.get('WEBHOOK_BACKOFF_FACTOR',
                                            BACKOFF_FACTOR))
                send(callback_url, metadata)
            except WebhookUnreachableException as e:
                logbook.error(('Webhook unreachable: {url} - {code} ({detail})'
                               .format(url=callback_url, code=e.code,
                                       detail=e.original_exception)))
