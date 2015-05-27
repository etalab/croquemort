import collections
import logbook
import redis
import requests

from nameko.events import event_handler

from tools import generate_hash

r = redis.StrictRedis(host='localhost', port=6379, db=0)
log = logbook.debug
FakeResponse = collections.namedtuple('Response', ['status_code', 'headers'])
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=50)
session.mount('http://', adapter)


class CrawlerService(object):
    name = 'url_crawler'
    headers = ('etag', 'last-modified', 'content-type', 'content-length')

    def store_data(self, url, url_hash, response):
        log('Storing {url}'.format(url=url))
        r.hset(url_hash, 'status', response.status_code)
        for header in self.headers:
            r.hset(url_hash, header, response.headers.get(header, ''))

    @event_handler('http_server', 'url_to_check')
    def check_url(self, url_group):
        url, group = url_group
        log('Checking {url} for group {group}'.format(url=url, group=group))
        url_hash = generate_hash(url)
        r.hset(url_hash, 'url', url)
        if group:
            group_hash = generate_hash(group)
            r.hset(url_hash, 'group', group_hash)
            r.hset(group_hash, 'name', group)
            r.hset(group_hash, url_hash, url)
        try:
            response = session.head(url)
        except requests.exceptions.ConnectionError:
            response = FakeResponse(status_code=503, headers={})
        except Exception, e:
            logbook.error('Error with {url}: {e}'.format(url=url, e=e))
        self.store_data(url, url_hash, response)
