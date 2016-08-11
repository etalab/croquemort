from datetime import datetime

import redis
from nameko.extensions import DependencyProvider
from kombu.utils.encoding import str_to_bytes

from .tools import generate_hash


REDIS_URI_KEY = 'REDIS_URI'
REDIS_DEFAULT_URI = 'redis://localhost:6379/5'
HEADERS = (
    'etag', 'expires', 'last-modified', 'content-type', 'content-length',
    'content-disposition', 'content-md5', 'content-encoding',
    'content-location'
)


class RedisStorage(DependencyProvider):

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
        return self.database.hgetall(str_to_bytes(group_hash))

    def delete_url(self, url_hash, data=None):
        if data is None:
            data = self.get_url(url_hash)
        for key in data:
            self.database.hdel(url_hash, key)
        self.database.lrem('urls', 0, url_hash)

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
            for header in HEADERS:
                value = response.headers.get(header, '')

                # Special treatment for content type which may contain charset.
                if header == 'content-type' and ';' in value:
                    self.store_content_type(url_hash, value)
                else:
                    self.database.hset(url_hash, header, str_to_bytes(value))

    def store_content_type(self, url_hash, value):
        try:
            content_type, charset = value.split(';')
        except ValueError:
            # Weird e.g.: text/html;h5ai=0.20;charset=UTF-8
            content_type, _, charset = value.split(';')

        value = content_type.strip().lower()
        if '=' in charset:
            _, charset = charset.split('=')
            self.database.hset(
                url_hash,
                'charset',
                str_to_bytes(charset.strip().lower()))
        self.database.hset(url_hash, 'content-type', str_to_bytes(value))

    def get_frequency_urls(self, frequency='hourly'):
        for group_hash in self.database.lrange(frequency, 0, -1):
            group_infos = self.get_group(group_hash)
            group_infos.pop('name')
            for url_hash, url in group_infos.iteritems():
                yield url

    def is_currently_checked(self, url, delay):  # In seconds.
        check_url_hash = 'check-{hash}'.format(hash=generate_hash(url))
        if self.database.exists(check_url_hash):
            return True
        else:
            self.database.set(check_url_hash, url)
            self.database.expire(check_url_hash, delay)
            return False

    def get_cache(self, key):
        return self.database.hgetall(str_to_bytes(key))

    def set_cache(self, key, content):
        self.database.hset(key, 'timestamp',
                           str_to_bytes(datetime.now().isoformat()))
        self.database.hset(key, 'content', str_to_bytes(content))

    def expire_cache(self, key, duration):
        self.database.expire(key, duration)
