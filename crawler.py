import collections
import logbook
import redis
import requests

from requests_futures.sessions import FuturesSession
from nameko.events import event_handler

from tools import generate_hash

r = redis.StrictRedis(host='localhost', port=6379, db=0)
log = logbook.debug
FakeResponse = collections.namedtuple('Response', ['status_code', 'headers'])
session = FuturesSession(max_workers=50)
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
    def check_url(self, url):
        log('Checking {url}'.format(url=url))
        url_hash = generate_hash(url)
        r.hset(url_hash, 'url', url)
        try:
            response = session.head(url)
        except requests.exceptions.ConnectionError:
            response = FakeResponse(status_code=503, headers={})
        except Exception, e:
            logbook.error('Error with {url}: {e}'.format(url=url, e=e))
        self.store_data(url, url_hash, response)

    @event_handler('http_server', 'urls_to_check')
    def check_urls(self, urls):
        log('Checking {length} URLs'.format(length=len(urls)))
        futures = (session.head(url) for url in urls)
        for url, future in zip(urls, futures):
            try:
                response = future.result()
            except requests.exceptions.ConnectionError:
                response = FakeResponse(status_code=503, headers={})
            except Exception, e:
                logbook.error('Error with {url}: {e}'.format(url=url, e=e))
            url_hash = generate_hash(url)
            self.store_data(url, url_hash, response)
