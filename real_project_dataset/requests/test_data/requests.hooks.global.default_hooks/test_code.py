def test_default_hooks():
    assert hooks.default_hooks() == {"response": []}

def test_prepared_request_with_hook_is_pickleable(self, httpbin):
        r = requests.Request("GET", httpbin("get"), hooks=default_hooks())
        p = r.prepare()
        r = pickle.loads(pickle.dumps(p))
        assert r.url == p.url
        assert r.headers == p.headers
        assert r.body == p.body
        assert r.hooks == p.hooks
        s = requests.Session()
        resp = s.send(r)
        assert resp.status_code == 200

@pytest.mark.parametrize(
    "data",
    (
        (("a", "b"), ("c", "d")),
        (("c", "d"), ("a", "b")),
        (("a", "b"), ("c", "d"), ("e", "f")),
    ),
)
def test_data_argument_accepts_tuples(data):
    p = PreparedRequest()
    p.prepare(
        method="GET", url="http://www.example.com", data=data, hooks=default_hooks()
    )
    assert p.body == urlencode(data)

@pytest.mark.parametrize(
    "kwargs",
    (
        None,
        {
            "method": "GET",
            "url": "http://www.example.com",
            "data": "foo=bar",
            "hooks": default_hooks(),
        },
        {
            "method": "GET",
            "url": "http://www.example.com",
            "data": "foo=bar",
            "hooks": default_hooks(),
            "cookies": {"foo": "bar"},
        },
        {"method": "GET", "url": "http://www.example.com/üniçø∂é"},
    ),
)
def test_prepared_copy(kwargs):
    p = PreparedRequest()
    if kwargs:
        p.prepare(**kwargs)
    copy = p.copy()
    for attr in ("method", "url", "headers", "_cookies", "body", "hooks"):
        assert getattr(p, attr) == getattr(copy, attr)