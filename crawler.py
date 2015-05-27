import collections
import logbook
import redis
import requests

from nameko.events import event_handler
from nameko.extensions import DependencyProvider

from tools import generate_hash

r = redis.StrictRedis(host='localhost', port=6379, db=0)
log = logbook.debug
FakeResponse = collections.namedtuple('Response', ['status_code', 'headers'])


class RequestsWrapper(object):

    def __init__(self, session):
        self.session = session

    def head(self, url):
        return self.session.head(url)


class SessionService(DependencyProvider):

    def setup(self):
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=20,
                                                pool_maxsize=50)
        self.session.mount('http://', adapter)

    def get_dependency(self, worker_ctx):
        return RequestsWrapper(self.session)


class CrawlerService(object):
    name = 'url_crawler'
    headers = ('etag', 'last-modified', 'content-type', 'content-length')
    session_service = SessionService()

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
            response = self.session_service.head(url)
        except requests.exceptions.ConnectionError:
            response = FakeResponse(status_code=503, headers={})
        except Exception, e:
            logbook.error('Error with {url}: {e}'.format(url=url, e=e))
        self.store_data(url, url_hash, response)

    @event_handler('http_server', 'urls_to_check')
    def check_urls(self, urls):
        log('Checking {length} URLs'.format(length=len(urls)))
        for url in urls:
            self.check_url(url)
