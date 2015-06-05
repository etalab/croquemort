import json
import hashlib

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
        raw = request.get_data().decode('utf-8')
        try:
            data = json.loads(raw or '{}')
        except ValueError as error:
            return 400, 'Incorrect parameters: {error}'.format(error=error)
        for parameter in parameters:
            if parameter not in data:
                log(('"{parameter}" parameter not found in {data}'
                     .format(data=data, parameter=parameter)))
                return 400, 'Please specify a "url" parameter.'
        args[0] = data
        return wrapped(*args, **kwargs)
    return wrapper


def generate_hash(value):
    """Custom hash to avoid long values."""
    return hashlib.md5(value.encode('utf-8')).hexdigest()[:8]


def extract_filters(querystring_dict):
    """Extracting filters and excludes from the querystring."""
    filter_prefix = 'filter_'
    exclude_prefix = 'exclude_'
    filters = {k[len(filter_prefix):]: v
               for (k, v) in querystring_dict.items()
               if k.startswith(filter_prefix)}
    excludes = {k[len(exclude_prefix):]: v
                for (k, v) in querystring_dict.items()
                if k.startswith(exclude_prefix)}
    if filters:
        log('Filtering results by {filters}'.format(filters=filters))
    if excludes:
        log('Excluding results by {excludes}'.format(excludes=excludes))
    return filters, excludes


def apply_filters(results, filters, excludes):
    """Return filtered results."""
    if filters:
        if all(results.get(prop) == value
               for prop, value in filters.items()):
            return results
    elif excludes:
        if all(results.get(prop) != value
               and results.get(prop) is not None
               for prop, value in excludes.items()
               if prop in results):
            return results
    else:
        return results
