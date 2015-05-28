import json

import pytest

from http import HttpService


@pytest.fixture
def web_session(container_factory, web_config, web_session):
    container = container_factory(HttpService, web_config)
    container.start()
    return web_session


def test_get_url(web_session):
    rv = web_session.get('/url', data=json.dumps({
        'url': 'http://example.org'
    }))
    assert rv.text == '{}'


def test_post_url(web_session):
    rv = web_session.post('/check/one', data=json.dumps({
        'url': 'http://example.org'
    }))
    assert rv.text == '{\n  "url-hash": 2039066596\n}'


def test_missing_parameter(web_session):
    rv = web_session.get('/url')
    assert rv.status_code == 400
    assert rv.text == 'Please specify a "url" parameter.'
