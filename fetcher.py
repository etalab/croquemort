import redis
import requests

from nameko.events import event_handler

r = redis.StrictRedis(host='localhost', port=6379, db=0)


class FetcherService(object):
    name = "url_fetcher"

    @event_handler("http_receiver", "url_to_check")
    def handle_event(self, url):
        print "FetcherService received", url
        url_hash = hash(url)
        response = requests.head(url)
        print(response.headers)
        r.hset(url_hash, 'url', url)
        r.hset(url_hash, 'status', response.status_code)
        print 'URL stored'
