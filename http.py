import json
import logbook
import redis

from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko.web.handlers import http

r = redis.StrictRedis(host='localhost', port=6379, db=0)


class HttpService(object):
    name = "http_server"
    dispatch = EventDispatcher()

    @http('GET', '/url/<int:url_hash>')
    def retrieve_url(self, request, url_hash):
        logbook.debug('Retrieving {hash}'.format(hash=url_hash))
        url_infos = r.hgetall(url_hash)
        logbook.debug('Grabing {infos}'.format(infos=url_infos))
        return json.dumps(url_infos, indent=2)

    @http('GET', '/group/<int:group_hash>')
    def retrieve_group(self, request, group_hash):
        logbook.debug('Retrieving {hash}'.format(hash=group_hash))
        group_infos = r.hgetall(group_hash)
        logbook.debug('Grabing {infos}'.format(infos=group_infos))
        infos = {'name': group_infos.pop('name')}
        for url_hash, url in group_infos.iteritems():
            infos[url] = r.hgetall(url_hash)
        return json.dumps(infos, indent=2)

    @http('POST', '/check/one')
    def check_one(self, request):
        data = json.loads(request.get_data())
        url = data.get('url', None)
        if url is None:
            logbook.debug(('"url" parameter not found in {data}'
                           .format(data=data)))
            return 400, 'Please specify a "url" parameter.'
        url_hash = hash(url)
        logbook.debug(('Checking "{url}" ({hash})'
                       .format(url=url, hash=url_hash)))
        self.fetch(url)
        return json.dumps({'url-hash': url_hash}, indent=2)

    @http('POST', '/check/many')
    def check_many(self, request):
        data = json.loads(request.get_data())
        urls = data.get('urls', None)
        if urls is None:
            logbook.debug(('"urls" parameter not found in {data}'
                           .format(data=data)))
            return 400, 'Please specify a "urls" parameter.'
        group = data.get('group', None)
        if group is None:
            logbook.debug(('"group" parameter not found in {data}'
                           .format(data=data)))
            return 400, 'Please specify a "group" parameter.'
        group_hash = hash(group)
        for url in urls:
            url_hash = hash(url)
            logbook.debug(('Checking "{url}" ({hash}) for group {group}'
                           .format(url=url, hash=url_hash, group=group)))
            r.hset(url_hash, 'group', group_hash)
            r.hset(group_hash, 'name', group)
            r.hset(group_hash, url_hash, url)
            self.fetch(url)
        return json.dumps({'group-hash': group_hash}, indent=2)

    @rpc
    def fetch(self, url):
        if r.hget(hash(url), 'url') is None:
            logbook.debug('URL unknown, checking {url}'.format(url=url))
            self.dispatch("url_to_check", url)
        else:
            logbook.debug('URL known, refreshing {url}'.format(url=url))
            self.dispatch("url_to_refresh", url)
