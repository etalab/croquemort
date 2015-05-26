import json
import redis

from nameko.web.handlers import http
from nameko.events import EventDispatcher
from nameko.rpc import rpc

r = redis.StrictRedis(host='localhost', port=6379, db=0)


class HttpService(object):
    name = "http_receiver"
    dispatch = EventDispatcher()

    @http('GET', '/url/<int:url_hash>')
    def retrieve(self, request, url_hash):
        return 'infos: {}'.format(r.hgetall(url_hash))

    @http('POST', '/check')
    def check(self, request):
        data = json.loads(request.get_data())
        url = data['url']
        url_hash = hash(url)
        self.fetch(url, url_hash)
        return "received: {}\nhash: {}".format(url, url_hash)

    @rpc
    def fetch(self, url, url_hash):
        url_infos = r.hget(url_hash, 'url')
        if url_infos is None:
            self.dispatch("url_to_check", url)
