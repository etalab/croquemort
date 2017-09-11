import json
from urllib.parse import urlencode

import logbook
from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko.web.handlers import http

from .decorators import cache_page, required_parameters
from .logger import LoggingDependency
from .reports import compute_csv, compute_report
from .storages import RedisStorage
from .tools import apply_filters, extract_filters, generate_hash

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
        group = data.get('group', None)
        log('Retrieving url {url} for group {group}'.format(
            url=url, group=group))
        self.fetch(url, group)  # Try again for later check.
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
    @required_parameters()
    def retrieve_group_from_hash(self, data, group_hash):
        log('Retrieving group hash {hash}'.format(hash=group_hash))
        group_infos = self.storage.get_group(group_hash)
        if not group_infos:
            return 404, ''
        group_infos.pop('url')
        infos = {'name': group_infos.pop('name')}
        filters, excludes = extract_filters(data)
        urls_infos = []
        for url_hash, url in group_infos.items():
            url_infos = self.storage.get_url(url_hash)
            results = apply_filters(url_infos, filters, excludes)
            if results:
                urls_infos.append(results)
        infos['urls'] = urls_infos
        log('Returning {num} results'.format(num=len(infos['urls'])))
        return json.dumps(infos, indent=2)

    @http('GET', '/')
    @required_parameters()
    @cache_page(60 * 60 * 2)  # Equals 2 hours.
    def display_report(self, data):
        log('Display report')
        all_urls = self.storage.get_all_urls()
        if not all_urls:
            return 404, ''
        querystring = urlencode(data)
        with_links = 'display_links' in data
        filters, excludes = extract_filters(data)
        return compute_report(
            all_urls, filters, excludes, querystring, with_links)

    @http('GET', '/robots.txt')
    def robots_txt(self, data):
        log('Disallow indexing from all robots')
        content = ['User-agent: *', 'Disallow: /']
        return '\n'.join(content)

    # No cache here given the response is streamed.
    @http('GET', '/csv')
    @required_parameters()
    def csv_report(self, data):
        log('CSV report')
        all_urls = self.storage.get_all_urls()
        if not all_urls:
            return 404, ''
        filters, excludes = extract_filters(data)
        return compute_csv(all_urls, filters, excludes)

    @http('POST', '/check/one')
    @required_parameters('url')
    def check_one(self, data):
        url = data.get('url')
        group = data.get('group', None)
        url_hash = generate_hash(url)
        log('Checking "{url}" ({hash}) in group "{group}"'.format(
            url=url, hash=url_hash, group=group))
        self.fetch(url, group=group)
        return json.dumps({'url-hash': url_hash}, indent=2)

    @http('POST', '/check/many')
    @required_parameters('urls', 'group')
    def check_many(self, data):
        urls = data.get('urls')
        group = data.get('group')
        group_hash = generate_hash(group)
        frequency = data.get('frequency', None)
        log(('Checking {num} URLs in group "{group}" ({hash}) '
             'with frequency "{frequency}"'.format(num=len(urls), group=group,
                                                   hash=group_hash,
                                                   frequency=frequency)))
        for url in urls:
            self.fetch(url, group, frequency)
        return json.dumps({'group-hash': group_hash}, indent=2)

    @rpc
    def fetch(self, url, group=None, frequency=None):
        log('Checking {url} for group "{group}"'.format(url=url, group=group))
        # Add a 3 hours delay before checking again,
        # avoid queuing too much checks for the same url.
        if not self.storage.is_currently_checked(url, delay=60 * 60 * 3):
            self.dispatch('url_to_check', (url, group, frequency))
        else:
            log('Check of {url} done not so long ago'.format(url=url))
