from croquemort.tools import apply_filters, extract_filters, generate_hash


def test_generate_hash():
    assert generate_hash('foo') == 'acbd18db'
    assert generate_hash('bar') == '37b51d19'


def test_extract_filters():
    assert extract_filters({}) == ({}, {})
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
