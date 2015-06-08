from datetime import datetime

import redis
from nameko.extensions import DependencyProvider
from kombu.utils.encoding import str_to_bytes

from .tools import generate_hash


REDIS_URI_KEY = 'REDIS_URI'
REDIS_DEFAULT_URI = 'redis://localhost:6379/0'


class RedisStorage(DependencyProvider):
    headers = (
        'etag', 'expires', 'last-modified',
        'content-type', 'content-length', 'content-disposition',
        'content-md5', 'content-encoding', 'content-location'
    )

    def setup(self):
        super(RedisStorage, self).setup()
        redis_uri = self.container.config.get(REDIS_URI_KEY, REDIS_DEFAULT_URI)

        self.database = redis.StrictRedis.from_url(redis_uri,
                                                   decode_responses=True,
                                                   charset='utf-8')

    def get_dependency(self, worker_ctx):
        return self

    def get_all_urls(self):
        for url_hash in self.database.lrange('urls', 0, -1):
            yield url_hash, self.get_url(url_hash)

    def get_url(self, url_hash):
        return self.database.hgetall(str_to_bytes(url_hash))

    def get_group(self, group_hash):
        return self.database.hgetall(group_hash)

    def store_url(self, url):
        url_hash = generate_hash(url)
        self.database.hset(url_hash, 'url', str_to_bytes(url))
        if url_hash not in self.database.lrange('urls', 0, -1):
            self.database.rpush('urls', str_to_bytes(url_hash))

    def store_group(self, url, group):
        url_hash = generate_hash(url)
        group_hash = generate_hash(group)
        self.database.hset(url_hash, 'group', str_to_bytes(group_hash))
        self.database.hset(group_hash, 'name', str_to_bytes(group))
        self.database.hset(group_hash, url_hash, str_to_bytes(url))
        self.database.hset(group_hash, 'url', str_to_bytes(url))

    def store_frequency(self, url, group, frequency):
        url_hash = generate_hash(url)
        group_hash = generate_hash(group)
        self.database.hset(url_hash, 'frequency', str_to_bytes(frequency))
        if group_hash not in self.database.lrange(frequency, 0, -1):
            self.database.rpush(frequency, str_to_bytes(group_hash))

    def store_metadata(self, url, response):
        url_hash = generate_hash(url)
        self.database.hset(url_hash, 'status',
                           str_to_bytes(response.status_code))
        self.database.hset(url_hash, 'updated',
                           str_to_bytes(datetime.now().isoformat()))
        if response.headers:
            for header in self.headers:
                self.database.hset(
                    url_hash, header,
                    str_to_bytes(response.headers.get(header, '')))

    def get_frequency_urls(self, frequency='hourly'):
        for group_hash in self.database.lrange(frequency, 0, -1):
            group_infos = self.get_group(group_hash)
            group_infos.pop('name')
            for url_hash, url in group_infos.iteritems():
                yield url
