import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta
from io import StringIO
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response

from .tools import apply_filters, retrieve_datetime

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
        status = data.get('final-status-code', '')
        if not status:
            continue

        # URLs.
        url = urlparse(data['checked-url'])
        if with_links:
            links.append(data['checked-url'])

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
            updated = retrieve_datetime(updated)
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


def compute_csv(urls, filters, excludes):
    """Generate a streamed CSV of all data, optionally filtered."""

    def generate():
        """A generator is required to stream the actual CSV."""
        fake_file = StringIO()
        w = csv.writer(fake_file)

        # Write the header.
        w.writerow(('URL', 'Status', 'Content-Type', 'Updated'))
        yield fake_file.getvalue()
        fake_file.seek(0)
        fake_file.truncate(0)

        for url_hash, data in urls:
            # Filtering.
            data = apply_filters(data, filters, excludes)
            if not data:
                continue

            # Statuses.
            status = data.get('final-status-code', '')
            if not status:
                continue

            url = data['checked-url']
            content_type = data.get('content-type', '')
            updated = data.get('updated', '')

            w.writerow((url, status, content_type, updated))
            yield fake_file.getvalue()
            fake_file.seek(0)
            fake_file.truncate(0)

    # Set headers with the appropriated filename.
    headers = Headers()
    headers.set('Content-Disposition', 'attachment',
                filename='croquemort-{date_iso}.csv'.format(
                    date_iso=datetime.now().date().isoformat()))

    # Stream the response as the data is generated.
    return Response(generate(), mimetype='text/csv', headers=headers)
