from unittest.mock import MagicMock

from croquemort.tools import (
    apply_filters, data_from_request, extract_filters, generate_hash
)


def test_data_from_request():
    assert data_from_request({'foo': 'bar'}) == {'foo': 'bar'}
    request = MagicMock()
    request.get_data = lambda: b'{"foo": "bar"}'
    assert data_from_request(request) == {'foo': 'bar'}


def test_generate_hash():
    assert generate_hash('foo') == 'acbd18db'
    assert generate_hash('bar') == '37b51d19'


def test_extract_filters():
    assert extract_filters({}) == ({}, {})
    assert extract_filters({'display_links': ''}) == ({}, {})
    assert extract_filters({'foo': 'bar'}) == ({}, {})
    assert extract_filters({'filter_foo': 'bar'}) == ({'foo': 'bar'}, {})
    assert extract_filters({'exclude_foo': 'bar'}) == ({}, {'foo': 'bar'})
    assert extract_filters({'filter_foo': ''}) == ({'foo': ''}, {})
    assert extract_filters({'exclude_foo': ''}) == ({}, {'foo': ''})


def test_apply_filters():
    assert apply_filters({}, {}, {}) == {}
    assert apply_filters({'foo': 'bar'}, {}, {}) == {'foo': 'bar'}
    assert apply_filters({'foo': 'bar'}, {'foo': 'bar'}, {}) == {'foo': 'bar'}
    assert apply_filters({'foo': 'bar'}, {}, {'foo': 'bar'}) is None
    assert apply_filters({'foo': 'bar'}, {'baz': 'quux'}, {}) is None
    assert apply_filters({'foo': 'bar'}, {'foo': 'quux'}, {}) is None
    assert apply_filters({'foo': 'bar'}, {}, {'foo': 'quux'}) == {'foo': 'bar'}
    assert apply_filters({'foo': 'bar'}, {}, {'baz': 'quux'}) == {'foo': 'bar'}


def test_apply_filters_with_domains():
    assert apply_filters(
        {'url': 'http://example.com/'}, {'domain': 'example.org'}, {}) is None
    input = {'url': 'http://example.org/'}
    assert apply_filters(input, {'domain': 'example.org'}, {}) == input
    assert apply_filters(input, {}, {'domain': 'example.org'}) is None
    input = {
        'url': 'http://example.com/',
        'status': '200',
    }
    assert apply_filters(
        input, {'domain': 'example.org', 'status': '200'}, {}) is None
    assert apply_filters(
        input, {'domain': 'example.org'}, {'status': '500'}) is None
    input = {
        'url': 'http://example.org/',
        'status': '200',
    }
    assert apply_filters(
        input, {'domain': 'example.org', 'status': '200'}, {}) == input
    assert apply_filters(
        input, {'domain': 'example.org', 'status': '400'}, {}) is None
    assert apply_filters(
        input, {'domain': 'example.org'}, {'status': '200'}) is None
    input = {
        'url': 'http://example.org/',
        'status': '200',
        'content-type': 'text/html',
    }
    assert apply_filters(
        input, {
            'domain': 'example.org',
            'status': '200',
            'content-type': 'text/html'
        }, {}) == input
    assert apply_filters(
        input,
        {'domain': 'example.org', 'status': '200'},
        {'content-type': 'text/html'}) is None
    assert apply_filters(
        input,
        {'domain': 'example.org', 'status': '500'},
        {'content-type': 'application/csv'}) is None
    assert apply_filters(
        input,
        {'domain': 'example.org'},
        {'content-type': 'application/csv', 'status': '500'}) == input
    assert apply_filters(
        input,
        {'domain': 'example.org', 'status': '200'},
        {'content-type': 'application/csv'}) == input
    assert apply_filters(
        input, {
            'status': '200',
            'content-type': 'text/html'
        }, {'domain': 'example.com'}) == input
    assert apply_filters(
        input,
        {'status': '200'},
        {'domain': 'example.org', 'content-type': 'application/csv'}) is None
    assert apply_filters(
        input,
        {'status': '500'},
        {'domain': 'example.com', 'content-type': 'application/csv'}) is None
    assert apply_filters(
        input,
        {}, {
            'domain': 'example.com',
            'content-type': 'application/csv',
            'status': '500'
        }) == input
    assert apply_filters(
        input,
        {'status': '200'},
        {'domain': 'example.com', 'content-type': 'application/csv'}) == input
