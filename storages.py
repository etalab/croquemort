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

    def store_metadata(self, url, response):
        url_hash = generate_hash(url)
        self.database.hset(url_hash, 'status', response.status_code)
        if response.headers:
            for header in self.headers:
                self.database.hset(url_hash, header,
                                   response.headers.get(header, ''))
