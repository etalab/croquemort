import json

import pytest

from croquemort.http import HttpService


@pytest.fixture
def web_session(container_factory, web_container_config, web_session):
    container = container_factory(HttpService, web_container_config)
    container.start()
    return web_session


def test_get_urls(web_session):
    rv = web_session.get('/')
    assert rv.text.startswith('<!doctype html>')
    assert rv.status_code == 200


def test_robots(web_session):
    rv = web_session.get('/robots.txt')
    assert rv.text == 'User-agent: *\nDisallow: /'
    assert rv.status_code == 200


def test_get_url(web_session):
    rv = web_session.get('/url', data=json.dumps({
        'url': 'http://example.org'
    }))
    assert rv.text == ''
    assert rv.status_code == 404


def test_get_group(web_session):
    rv = web_session.get('/group', data=json.dumps({
        'group': 'mygroup'
    }))
    assert rv.text == ''
    assert rv.status_code == 404


def test_get_url_from_hash(web_session):
    rv = web_session.get('/url/myhash')
    assert rv.text == ''
    assert rv.status_code == 404


def test_get_group_from_hash(web_session):
    rv = web_session.get('/group/myhash')
    assert rv.text == ''
    assert rv.status_code == 404


def test_post_url(web_session):
    rv = web_session.post('/check/one', data=json.dumps({
        'url': 'http://example.org'
    }))
    assert rv.json()['url-hash'] == 'dab521de'
    assert rv.status_code == 200


def test_post_urls(web_session):
    rv = web_session.post('/check/many', data=json.dumps({
        'urls': ['http://example.org', 'http://example.com'],
        'group': 'datagouvfr'
    }))
    assert rv.json()['group-hash'] == 'efcf3897'
    assert rv.status_code == 200


def test_missing_parameter(web_session):
    rv = web_session.get('/url')
    assert rv.status_code == 400
    assert rv.text == 'Please specify a "url" parameter.'
