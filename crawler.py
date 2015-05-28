import collections
import logbook
import requests

from nameko.events import event_handler

from logger import LoggingDependency
from storages import RedisStorage

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
    def check_url(self, url_group):
        url, group = url_group
        log('Checking {url} for group {group}'.format(url=url, group=group))
        self.storage.store_url(url)
        if group:
            self.storage.store_group(url, group)
        try:
            response = session.head(url)
        except requests.exceptions.ConnectionError:
            response = FakeResponse(status_code=503, headers={})
        except Exception, e:
            logbook.error('Error with {url}: {e}'.format(url=url, e=e))
        self.storage.store_metadata(url, response)
