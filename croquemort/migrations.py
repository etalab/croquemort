from urllib.parse import urlparse

import logging
from nameko.rpc import rpc

from .logger import LoggingDependency
from .storages import RedisStorage
from .tools import HASH_PREFIXES

log = logging.info


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

    def _get_hash_prefixes(self):
        """Helper method for add_hash_prefixes"""
        return ('{}:'.format(HASH_PREFIXES['url']),
                '{}:'.format(HASH_PREFIXES['group']))

    def _migrate_group(self, key):
        """Used by `add_hash_prefixes` to migrate a group"""
        url_prefix, group_prefix = self._get_hash_prefixes()
        new_hash = '{}{}'.format(group_prefix, key)
        log('Renaming group {} to {}'.format(key, new_hash))
        self.storage.database.rename(key, new_hash)
        group_info = self.storage.get_group(new_hash)
        group_info.pop('name')
        group_info.pop('url', None)
        for u_hash, url in group_info.items():
            # set new url hash field
            self.storage.database.hset(
                new_hash, '{}{}'.format(url_prefix, u_hash), url)
            # remove old url hash field
            self.storage.database.hdel(new_hash, u_hash)

    def _migrate_url(self, key, data):
        """Used by `add_hash_prefixes` to migrate a url"""
        url_prefix, group_prefix = self._get_hash_prefixes()
        new_hash = '{}{}'.format(url_prefix, key)
        log('Renaming url {} to {}'.format(key, new_hash))
        self.storage.database.rename(key, new_hash)
        if 'group' in data:
            new_g_hash = '{}{}'.format(group_prefix, data['group'])
            self.storage.database.hset(new_hash, 'group', new_g_hash)

    def _migrate_urls_list(self):
        """Used by `add_hash_prefixes` to migrate the url list"""
        log('Migration urls list')
        database = self.storage.database
        url_prefix, group_prefix = self._get_hash_prefixes()
        for idx, url_hash in enumerate(database.lrange('urls', 0, -1)):
            new_hash = '{}{}'.format(url_prefix, url_hash)
            database.lset('urls', idx, new_hash)

    def _migrate_frequency(self, key):
        """Used by `add_hash_prefixes` to migrate a frequency"""
        database = self.storage.database
        url_prefix, group_prefix = self._get_hash_prefixes()
        for idx, g_hash in enumerate(database.lrange(key, 0, -1)):
            if not g_hash.startswith(group_prefix):
                log('Handling group {} for freq {}'.format(g_hash, key))
                database.lset(key, idx, '{}{}'.format(group_prefix,
                                                      g_hash))

    @rpc
    def add_hash_prefixes(self):
        """
        [migration from 1.0.0 to 2.0.0]

        Add url and group hash prefixes where they are missing:
        - /urls[<uhash>] -> /urls[<u:uhash>]
        - /<uhash> -> /<u:uhash>
        - /<u:uhash>/group=<ghash> -> /<u:uhash>/group=<g:ghash>
        - /<frequency>[<ghash>] -> /<frequency>[<g:ghash>]
        - /<ghash> -> /<g:ghash>
        - /<g:ghash>/<uhash> -> /<g:ghash>/<u:uhash>

        NB1: checks are not migrated because they expire quite fast
        NB2: should be idempotent
        """
        log('Adding hash prefixes')
        database = self.storage.database
        url_prefix, group_prefix = self._get_hash_prefixes()
        for key in database.scan_iter():
            if database.type(key) == 'hash' \
                    and not key.startswith('cache-') \
                    and not key.startswith('check-') \
                    and not key.startswith(url_prefix) \
                    and not key.startswith(group_prefix):
                data = database.hgetall(key)
                if data.get('name'):
                    self._migrate_group(key)
                elif data.get('url'):
                    self._migrate_url(key, data)
                else:
                    log('/!\ unknown hash type at key {}'.format(key))
        self._migrate_urls_list()
        for freq in ['hourly', 'daily', 'monthly']:
            self._migrate_frequency(freq)

    @rpc
    def migrate_urls_redirect(self):
        """
        [migration from 1.0.0 to 2.0.0]

        Migrate all the url hash fields to the new schema adopted with the
        "redirect handling" feature. We do not fill `final-url` for stock data
        because we have no way to know if a redirection has been made.

        Plus, cleanup url hashes with no url field attached.

        NB: should be idempotent
        """
        database = self.storage.database
        for url_hash, data in self.storage.get_all_urls():
            if data.get('checked-url'):
                continue
            if data.get('url'):
                database.hset(url_hash, 'checked-url', data['url'])
                database.hdel(url_hash, 'url')
                if data.get('status'):
                    database.hset(url_hash, 'final-status-code',
                                  data['status'])
                    database.hdel(url_hash, 'status')
                else:
                    log('Missing status for hash %s (%s)' % (url_hash, data))
            else:
                log('No url for hash %s (%s) - deleting' % (url_hash, data))
                database.delete(url_hash)
