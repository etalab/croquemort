import json
import hashlib
from datetime import datetime
from urllib.parse import urlparse

import logbook

log = logbook.debug

# /!\ dict values should be kept unique for sanity
HASH_PREFIXES = {
    'url': 'u',
    'group': 'g',
    'check': 'c',
}


def data_from_request(request):
    """Return a dict of data from a JSON request, idempotent."""
    if isinstance(request, dict):
        return request
    raw = request.get_data().decode('utf-8')
    return json.loads(raw or '{}')


def flatten_get_parameters(request):
    """Return a dict with flattened GET parameters.

    Otherwise a dict(ImmutableMultiDict) returns a list for each
    parameter value and that is not what we want in most of the cases.
    """
    if not hasattr(request, 'args'):
        return {}
    return {k: len(v) == 1 and v[0] or v
            for k, v in dict(request.args).items()}


def _generate_hash(value):
    """Custom hash to avoid long values."""
    return hashlib.md5(value.encode('utf-8')).hexdigest()[:8]


def generate_hash_for(hash_type, value):
    """Return a hash prefixed for hash_type"""
    prefix = HASH_PREFIXES.get(hash_type)
    if not prefix:
        raise Exception('Unknown hash_type {}'.format(hash_type))
    return '{}:{}'.format(prefix, _generate_hash(value))


def extract_filters(querystring_dict):
    """Extracting filters and excludes from the querystring."""
    if 'display_links' in querystring_dict:
        del querystring_dict['display_links']
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


def apply_filters(data, filters, excludes):
    """Return filtered data."""
    filters = filters.copy()
    excludes = excludes.copy()
    has_domain_filter = 'domain' in filters
    has_domain_exclude = 'domain' in excludes
    has_domain = has_domain_filter or has_domain_exclude
    filtered_domain = (
        has_domain_filter
        and urlparse(data['url']).netloc == filters.pop('domain'))
    excluded_domain = (
        has_domain_exclude
        and urlparse(data['url']).netloc == excludes.pop('domain'))
    kept_domain = ((has_domain_filter and filtered_domain)
                   or (has_domain_exclude and not excluded_domain))
    has_props = all(data.get(prop) == value
                    for prop, value in filters.items())
    has_not_props = all(data.get(prop) != value
                        and data.get(prop) is not None
                        for prop, value in excludes.items()
                        if prop in data)
    if has_domain and not kept_domain:
        return
    elif filters and excludes and not has_props or not has_not_props:
        return
    elif filters and not has_props:
        return
    elif excludes and not has_not_props:
        return
    return data


def retrieve_datetime(datetime_isoformat):
    try:
        return datetime.strptime(datetime_isoformat, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(datetime_isoformat, "%Y-%m-%dT%H:%M:%S")
