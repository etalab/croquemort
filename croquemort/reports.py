import os
from collections import defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse

from werkzeug.wrappers import Response
from jinja2 import Environment, FileSystemLoader

from .tools import apply_filters

template_path = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(loader=FileSystemLoader(template_path), autoescape=True)

# Flat UI colors from http://flatuicolors.co/
COLORS = [
    '#1ABC9C', '#16A085', '#2ECC71', '#27AE60', '#3498DB', '#2980B9',
    '#9B59B6', '#8E44AD', '#34495E', '#2C3E50', '#F1C40F', '#F39C12',
    '#E67E22', '#D35400', '#E74C3C', '#C0392B', '#ECF0F1', '#BDC3C7',
    '#95A5A6', '#7F8C8D',
]


def compute_report(urls, filters, excludes, querystring, with_links=False):
    count = 0
    colors = COLORS * 4  # Be sure to have enough colors.
    availability = 0
    statuses = defaultdict(int)
    content_types = defaultdict(int)
    schemes = defaultdict(int)
    updates = defaultdict(int)
    domains = defaultdict(dict)
    links = []
    filtered = filters or excludes
    today = datetime.today()
    for url_hash, data in urls:
        # Filtering.
        data = apply_filters(data, filters, excludes)
        if not data:
            continue

        # Statuses.
        status = data.get('status', '')  # TODO: check why no status?
        if not status:
            continue

        # URLs.
        url = urlparse(data['url'])
        if with_links:
            links.append(data['url'])

        statuses[status] += 1
        schemes[url.scheme] += 1
        domains[url.netloc].setdefault('count', 0)
        domains[url.netloc]['count'] += 1
        if int(status) < 400:
            domains[url.netloc].setdefault('valid', 0)
            domains[url.netloc]['valid'] += 1
            availability += 1

        # Content types.
        content_type = data.get('content-type', '')
        if content_type:
            content_types[content_type] += 1

        # Updates.
        updated = data.get('updated', '')
        if updated:
            updated = datetime.strptime(updated, "%Y-%m-%dT%H:%M:%S.%f")
            if (updated + timedelta(days=1)) > today:
                updates['Today'] += 1
            elif (updated + timedelta(days=7)) > today:
                updates['This week'] += 1
            elif (updated + timedelta(days=30)) > today:
                updates['This month'] += 1
            elif (updated + timedelta(days=365)) > today:
                updates['This year'] += 1

        count += 1
    availability = count and round(availability / count * 100, 2) or 0
    context = {
        'round': round,
        'count': count,
        'colors': colors,
        'querystring': querystring,
        'filtered': filtered,
        'links': links,
        'availability': availability,
        'updates': sorted(updates.items()),
        'statuses': sorted(statuses.items()),
        'content_types': sorted(content_types.items()),
        'schemes': sorted(schemes.items()),
        'domains': sorted(list(domains.items()),
                          key=lambda a: a[1]['count'], reverse=True)[:20]
    }
    template = env.get_template('report.html')
    return Response(template.render(context), mimetype='text/html')
