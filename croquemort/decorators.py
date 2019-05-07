import logging
import wrapt

from .tools import data_from_request, flatten_get_parameters

log = logging.info


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
