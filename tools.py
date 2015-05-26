
def generate_hash(value):
    """Custom hash to avoid negative values.

    See http://stackoverflow.com/a/2688025 for details.
    """
    return hash(value) & ((1 << 32)-1)
