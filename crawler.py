import logbook
import redis
import requests

from nameko.events import event_handler

r = redis.StrictRedis(host='localhost', port=6379, db=0)


class CrawlerService(object):
    name = "url_crawler"

    @event_handler("http_server", "url_to_check")
    def check_url(self, url):
        logbook.debug('Receiving {url}'.format(url=url))
        url_hash = hash(url)
        response = requests.head(url)
        logbook.debug('Headers: {headers}'.format(headers=response.headers))
        r.hset(url_hash, 'url', url)
        r.hset(url_hash, 'status', response.status_code)
        r.hset(url_hash, 'content-type',
               response.headers.get('content-type', ''))
        logbook.debug('Storing {url}'.format(url=url))

    @event_handler("http_server", "url_to_refresh")
    def refresh_url(self, url):
        logbook.debug('Receiving {url}'.format(url=url))
        url_hash = hash(url)
        response = requests.head(url)
        logbook.debug('Headers: {headers}'.format(headers=response.headers))
        r.hset(url_hash, 'status', response.status_code)
        r.hset(url_hash, 'content-type',
               response.headers.get('content-type', ''))
        logbook.debug('Updating {url}'.format(url=url))
