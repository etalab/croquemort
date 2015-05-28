import json
import logbook

from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko.web.handlers import http

from logger import LoggingDependency
from storages import RedisStorage
from tools import generate_hash, required_parameters

log = logbook.debug


class HttpService(object):
    name = 'http_server'
    dispatch = EventDispatcher()
    storage = RedisStorage()
    logger = LoggingDependency(interval='ms')

    @http('GET', '/url')
    @required_parameters('url')
    def retrieve_url(self, data):
        url = data.get('url')
        log('Retrieving {url}'.format(url=url))
        return self.retrieve_url_from_hash(data, generate_hash(url))

    @http('GET', '/url/<int:url_hash>')
    def retrieve_url_from_hash(self, request, url_hash):
        log('Retrieving url {hash}'.format(hash=url_hash))
        url_infos = self.storage.get_url(url_hash)
        log('Grabing {infos}'.format(infos=url_infos))
        return json.dumps(url_infos, indent=2)

    @http('GET', '/group/<int:group_hash>')
    def retrieve_group_from_hash(self, request, group_hash):
        log('Retrieving group {hash}'.format(hash=group_hash))
        data = json.loads(request.get_data() or '{}')
        filters = {k.lstrip('filter_'): v for (k, v) in data.iteritems()}
        if filters:
            log('Filtering results by {filters}'.format(filters=filters))
        group_infos = self.storage.get_group(group_hash)
        infos = {'name': group_infos.pop('name')}
        for url_hash, url in group_infos.iteritems():
            url_infos = self.storage.get_url(url_hash)
            if filters:
                if all(url_infos.get(prop, None) == value
                       for prop, value in filters.iteritems()):
                    infos[url_hash] = url_infos
            else:
                infos[url_hash] = url_infos
        return json.dumps(infos, indent=2)

    @http('POST', '/check/one')
    @required_parameters('url')
    def check_one(self, data):
        url = data.get('url')
        url_hash = generate_hash(url)
        log('Checking "{url}" ({hash})'.format(url=url, hash=url_hash))
        self.fetch(url)
        return json.dumps({'url-hash': url_hash}, indent=2)

    @http('POST', '/check/many')
    @required_parameters('urls', 'group')
    def check_many(self, data):
        urls = data.get('urls')
        group = data.get('group')
        group_hash = generate_hash(group)
        frequency = data.get('frequency', None)
        log(('Checking "{group}" ({hash}) with frequency "{frequency}"'
             .format(group=group, hash=group_hash, frequency=frequency)))
        for url in urls:
            self.fetch(url, group, frequency)
        return json.dumps({'group-hash': group_hash}, indent=2)

    @rpc
    def fetch(self, url, group=None, frequency=None):
        log('Checking {url} for group "{group}"'.format(url=url, group=group))
        self.dispatch('url_to_check', (url, group, frequency))
