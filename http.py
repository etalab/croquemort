import json
import logbook
import redis

from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko.web.handlers import http

from tools import generate_hash

r = redis.StrictRedis(host='localhost', port=6379, db=0)
log = logbook.debug


class HttpService(object):
    name = 'http_server'
    dispatch = EventDispatcher()

    @http('GET', '/url')
    def retrieve_url(self, request):
        data = json.loads(request.get_data())
        url = data.get('url', None)
        if url is None:
            log('"url" parameter not found in {data}'.format(data=data))
            return 400, 'Please specify a "url" parameter.'
        log('Retrieving {url}'.format(url=url))
        return self.retrieve_url_from_hash(request, generate_hash(url))

    @http('GET', '/url/<int:url_hash>')
    def retrieve_url_from_hash(self, request, url_hash):
        log('Retrieving url {hash}'.format(hash=url_hash))
        url_infos = r.hgetall(url_hash)
        log('Grabing {infos}'.format(infos=url_infos))
        return json.dumps(url_infos, indent=2)

    @http('GET', '/group/<int:group_hash>')
    def retrieve_group_from_hash(self, request, group_hash):
        data = json.loads(request.get_data() or '{}')
        filters = {k.lstrip('filter_'): v for (k, v) in data.iteritems()}
        log('Retrieving group {hash}'.format(hash=group_hash))
        group_infos = r.hgetall(group_hash)
        log('Grabing {infos}'.format(infos=group_infos))
        infos = {'name': group_infos.pop('name')}
        for url_hash, url in group_infos.iteritems():
            url_infos = r.hgetall(url_hash)
            if filters:
                log('Filtering results by {filters}'.format(filters=filters))
                if all(url_infos.get(prop, None) == value
                       for prop, value in filters.iteritems()):
                    infos[url] = url_infos
            else:
                infos[url] = url_infos
        return json.dumps(infos, indent=2)

    @http('POST', '/check/one')
    def check_one(self, request):
        data = json.loads(request.get_data())
        url = data.get('url', None)
        if url is None:
            log('"url" parameter not found in {data}'.format(data=data))
            return 400, 'Please specify a "url" parameter.'
        url_hash = generate_hash(url)
        log('Checking "{url}" ({hash})'.format(url=url, hash=url_hash))
        self.fetch(url)
        return json.dumps({'url-hash': url_hash}, indent=2)

    @http('POST', '/check/many')
    def check_many(self, request):
        data = json.loads(request.get_data())
        urls = data.get('urls', None)
        if urls is None:
            log('"urls" parameter not found in {data}'.format(data=data))
            return 400, 'Please specify a "urls" parameter.'
        group = data.get('group', None)
        if group is None:
            log('"group" parameter not found in {data}'.format(data=data))
            return 400, 'Please specify a "group" parameter.'
        group_hash = generate_hash(group)
        for url in urls:
            url_hash = generate_hash(url)
            log(('Checking "{url}" ({hash}) for group {group}'
                 .format(url=url, hash=url_hash, group=group)))
            self.fetch(url, group)
        return json.dumps({'group-hash': group_hash}, indent=2)

    @rpc
    def fetch(self, url, group=None):
        if group is not None:
            group_hash = generate_hash(group)
            url_hash = generate_hash(url)
            r.hset(url_hash, 'group', group_hash)
            r.hset(group_hash, 'name', group)
            r.hset(group_hash, url_hash, url)
        if r.hget(generate_hash(url), 'url') is None:
            log('URL unknown, checking {url}'.format(url=url))
            self.dispatch('url_to_check', url)
        else:
            log('URL known, refreshing {url}'.format(url=url))
            self.dispatch('url_to_refresh', url)
