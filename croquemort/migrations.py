from urllib.parse import urlparse

import logbook
from nameko.rpc import rpc

from .logger import LoggingDependency
from .storages import RedisStorage

log = logbook.debug


class MigrationsService(object):
    name = 'migrations'
    storage = RedisStorage()
    logger = LoggingDependency(interval='ms')

    @rpc
    def delete_urls_for(self, domain):
        log('Deleting URLs for domain {domain}'.format(domain=domain))
        for url_hash, data in self.storage.get_all_urls():
            if data and urlparse(data['url']).netloc == domain:
                self.storage.delete_url(url_hash)

    @rpc
    def split_content_types(self):
        log('Splitting content types')
        for url_hash, data in self.storage.get_all_urls():
            content_type = data.get('content-type')
            if content_type and ';' in content_type:
                self.storage.store_content_type(url_hash, content_type)
