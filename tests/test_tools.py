from croquemort.tools import generate_hash


def test_generate_hash():
    assert generate_hash('foo') == 'acbd18db'
    assert generate_hash('bar') == '37b51d19'
