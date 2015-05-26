import logbook
import redis
import requests

from nameko.events import event_handler

from tools import generate_hash

r = redis.StrictRedis(host='localhost', port=6379, db=0)


class CrawlerService(object):
    name = "url_crawler"

    def store_data(self, url, url_hash, response):
        r.hset(url_hash, 'status', response.status_code)
        r.hset(url_hash, 'etag',
               response.headers.get('etag', ''))
        r.hset(url_hash, 'last-modified',
               response.headers.get('last-modified', ''))
        r.hset(url_hash, 'content-type',
               response.headers.get('content-type', ''))
        r.hset(url_hash, 'content-length',
               response.headers.get('content-length', ''))
        logbook.debug('Storing {url}'.format(url=url))

    @event_handler("http_server", "url_to_check")
    def check_url(self, url):
        logbook.debug('Checking {url}'.format(url=url))
        url_hash = generate_hash(url)
        response = requests.head(url)
        logbook.debug('Headers: {headers}'.format(headers=response.headers))
        r.hset(url_hash, 'url', url)
        self.store_data(url, url_hash, response)

    @event_handler("http_server", "url_to_refresh")
    def refresh_url(self, url):
        logbook.debug('Refreshing {url}'.format(url=url))
        url_hash = generate_hash(url)
        response = requests.head(url)
        logbook.debug('Headers: {headers}'.format(headers=response.headers))
        self.store_data(url, url_hash, response)
