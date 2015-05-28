from tools import generate_hash


def test_generate_hash():
    assert generate_hash('foo') == 3554576059
    assert generate_hash('bar') == 3827942500
