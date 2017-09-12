

def filter_mock_requests(url, requests_l):
    return [r for r in requests_l if url in r.url]
