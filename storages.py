from datetime import datetime

import redis
from nameko.extensions import DependencyProvider

from tools import generate_hash


class RedisStorage(DependencyProvider):
    headers = ('etag', 'last-modified', 'content-type', 'content-length')

    def __init__(self):
        self.database = redis.StrictRedis(host='localhost', port=6379, db=0)

    def get_dependency(self, worker_ctx):
        return self

    def get_url(self, url_hash):
        return self.database.hgetall(url_hash)

    def get_group(self, group_hash):
        return self.database.hgetall(group_hash)

    def store_url(self, url):
        url_hash = generate_hash(url)
        self.database.hset(url_hash, 'url', url)

    def store_group(self, url, group):
        url_hash = generate_hash(url)
        group_hash = generate_hash(group)
        self.database.hset(url_hash, 'group', group_hash)
        self.database.hset(group_hash, 'name', group)
        self.database.hset(group_hash, url_hash, url)
        self.database.hset(group_hash, 'url', url)

    def store_frequency(self, url, group, frequency):
        url_hash = generate_hash(url)
        group_hash = generate_hash(group)
        self.database.hset(url_hash, 'frequency', frequency)
        if group_hash not in self.database.lrange(frequency, 0, -1):
            self.database.rpush(frequency, group_hash)

    def store_metadata(self, url, response):
        url_hash = generate_hash(url)
        self.database.hset(url_hash, 'status', response.status_code)
        self.database.hset(url_hash, 'updated', datetime.now().isoformat())
        if response.headers:
            for header in self.headers:
                self.database.hset(url_hash, header,
                                   response.headers.get(header, ''))

    def get_frequency_urls(self, frequency='hourly'):
        for group_hash in self.database.lrange(frequency, 0, -1):
            group_infos = self.get_group(group_hash)
            group_infos.pop('name')
            for url_hash, url in group_infos.iteritems():
                yield url
