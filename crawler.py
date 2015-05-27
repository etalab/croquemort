import logbook
import redis
import requests

from nameko.events import event_handler

from tools import generate_hash

r = redis.StrictRedis(host='localhost', port=6379, db=0)
log = logbook.debug


class CrawlerService(object):
    name = 'url_crawler'
    headers = ('etag', 'last-modified', 'content-type', 'content-length')

    def store_data(self, url, url_hash, response):
        r.hset(url_hash, 'status', response.status_code)
        for header in self.headers:
            r.hset(url_hash, header, response.headers.get(header, ''))
        log('Storing {url}'.format(url=url))

    @event_handler('http_server', 'url_to_check')
    def check_url(self, url):
        log('Checking {url}'.format(url=url))
        url_hash = generate_hash(url)
        response = requests.head(url)
        log(('Headers: {headers} with status {status}'
             .format(headers=response.headers, status=response.status_code)))
        r.hset(url_hash, 'url', url)
        self.store_data(url, url_hash, response)

    @event_handler('http_server', 'url_to_refresh')
    def refresh_url(self, url):
        log('Refreshing {url}'.format(url=url))
        url_hash = generate_hash(url)
        response = requests.head(url)
        log(('Headers: {headers} with status {status}'
             .format(headers=response.headers, status=response.status_code)))
        self.store_data(url, url_hash, response)
