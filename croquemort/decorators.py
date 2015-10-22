from datetime import datetime, timedelta
from urllib.parse import urlencode

import logbook
import redis
import wrapt
from werkzeug.wrappers import Response

from .storages import RedisStorage
from .tools import data_from_request, flatten_get_parameters

log = logbook.debug


def required_parameters(*parameters):
    """A decorator for views with required parameters.

    Returns a 400 if parameters are not provided by the client.

    Warning: when applied, it turns the request object into a data one,
    as first parameter of the returned function to avoid parsing the
    JSON data twice.
    """
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        args = list(args)
        request = args[0]
        try:
            data = data_from_request(request)
        except ValueError as error:
            return 400, 'Incorrect parameters: {error}'.format(error=error)
        data.update(flatten_get_parameters(request))
        for parameter in parameters:
            if parameter not in data:
                log(('"{parameter}" parameter not found in {data}'
                     .format(data=data, parameter=parameter)))
                return 400, ('Please specify a "{parameter}" parameter.'
                             .format(data=data, parameter=parameter))
        args[0] = data
        return wrapped(*args, **kwargs)
    return wrapper


def cache_page(duration):
    """A decorator for caching a view given parameters.

    The cache is effective during `duration` seconds.
    """
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        args = list(args)
        data = args[0]
        storage = RedisStorage()
        # TODO: should depends on the configuration.
        redis_uri = 'redis://localhost:6379/5'
        storage.database = redis.StrictRedis.from_url(redis_uri,
                                                      decode_responses=True,
                                                      charset='utf-8')
        key = 'cache-{data}'.format(data=urlencode(data))
        cached = storage.get_cache(key)
        if cached:
            timestamp = datetime.strptime(cached['timestamp'],
                                          '%Y-%m-%dT%H:%M:%S.%f')
            if timestamp + timedelta(seconds=duration) > datetime.now():
                return Response(cached['content'], mimetype='text/html')
        response = wrapped(*args, **kwargs)
        storage.set_cache(key, response.response[0])
        return response
    return wrapper
