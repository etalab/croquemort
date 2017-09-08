import re

import collections
import logbook
import requests

from nameko.events import event_handler

from .logger import LoggingDependency
from .storages import RedisStorage

HEAD_TIMEOUT = 10  # in seconds
GET_TIMEOUT = 3 * 60  # in seconds

# See https://github.com/kvesteri/validators for reference.
url_pattern = re.compile(
    r'^[a-z]+://([^/:]+\.[a-z]{2,10}|([0-9]{{1,3}}\.)'
    r'{{3}}[0-9]{{1,3}})(:[0-9]+)?(\/.*)?$'
)

log = logbook.debug
FakeResponse = collections.namedtuple('Response', ['status_code', 'headers'])
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=50)
session.mount('http://', adapter)


class CrawlerService(object):
    name = 'url_crawler'
    storage = RedisStorage()
    logger = LoggingDependency()

    @event_handler('http_server', 'url_to_check')
    @event_handler('timer', 'url_to_check')
    def check_url(self, url_group_frequency):
        url, group, frequency = url_group_frequency
        log(('Checking {url} for group {group} and frequency "{frequency}"'
             .format(url=url, group=group, frequency=frequency)))
        if not url_pattern.match(url):
            logbook.error('Error with {url}: not a URL'.format(url=url))
            return
        self.storage.store_url(url)
        if group:
            self.storage.store_group(url, group)
            if frequency:
                self.storage.store_frequency(url, group, frequency)
        try:
            try:
                response = session.head(url, allow_redirects=True,
                                        timeout=HEAD_TIMEOUT)
            except requests.exceptions.ReadTimeout:
                # simulate 404 to trigger GET request below
                response = FakeResponse(status_code=404, headers={})
            # Double check for servers not dealing properly with HEAD.
            if response.status_code in (400, 404, 405):
                log('Checking {url} with a GET'.format(url=url))
                response = session.get(url, allow_redirects=True,
                                       timeout=GET_TIMEOUT, stream=True)
                response.close()
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout):
            response = FakeResponse(status_code=503, headers={})
        except Exception as e:
            logbook.error('Error with {url}: {e}'.format(url=url, e=e))
            return
        self.storage.store_metadata(url, response)
