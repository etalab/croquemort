import json
import logbook
import wrapt

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
        data = json.loads(request.get_data() or '{}')
        for parameter in parameters:
            if parameter not in data:
                log(('"{parameter}" parameter not found in {data}'
                     .format(data=data, parameter=parameter)))
                return 400, 'Please specify a "url" parameter.'
        args[0] = data
        return wrapped(*args, **kwargs)
    return wrapper


def generate_hash(value):
    """Custom hash to avoid negative values.

    See http://stackoverflow.com/a/2688025 for details.
    """
    return hash(value) & ((1 << 32)-1)
