import json

import logbook
from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko.web.handlers import http

from .logger import LoggingDependency
from .storages import RedisStorage
from .tools import (
    apply_filters, extract_filters, generate_hash, required_parameters
)

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
        log('Retrieving url {url}'.format(url=url))
        return self.retrieve_url_from_hash(data, generate_hash(url))

    @http('GET', '/url/<url_hash>')
    def retrieve_url_from_hash(self, request_or_data, url_hash):
        log('Retrieving url hash {hash}'.format(hash=url_hash))
        url_infos = self.storage.get_url(url_hash)
        if not url_infos:
            return 404, ''
        log('Grabing {infos}'.format(infos=url_infos))
        return json.dumps(url_infos, indent=2)

    @http('GET', '/group')
    @required_parameters('group')
    def retrieve_group(self, data):
        group = data.get('group')
        log('Retrieving group {group}'.format(group=group))
        return self.retrieve_group_from_hash(data, generate_hash(group))

    @http('GET', '/group/<group_hash>')
    def retrieve_group_from_hash(self, request_or_data, group_hash):
        log('Retrieving group hash {hash}'.format(hash=group_hash))
        if isinstance(request_or_data, dict):
            data = request_or_data
        else:
            request_data = request_or_data.get_data().decode('utf-8')
            data = json.loads(request_data or '{}')
        group_infos = self.storage.get_group(group_hash)
        if not group_infos:
            return 404, ''
        group_infos.pop('url')
        infos = {'name': group_infos.pop('name')}
        filters, excludes = extract_filters(data)
        for url_hash, url in group_infos.items():
            url_infos = self.storage.get_url(url_hash)
            results = apply_filters(url_infos, filters, excludes)
            if results:
                infos[url_hash] = results
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
