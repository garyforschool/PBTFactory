def test_is_resource_modified(self):
        env = create_environ()
        env["REQUEST_METHOD"] = "POST"
        assert http.is_resource_modified(env, etag="testing")
        env["REQUEST_METHOD"] = "GET"
        pytest.raises(TypeError, http.is_resource_modified, env, data="42", etag="23")
        env["HTTP_IF_NONE_MATCH"] = http.generate_etag(b"awesome")
        assert not http.is_resource_modified(env, data=b"awesome")
        env["HTTP_IF_MODIFIED_SINCE"] = http.http_date(datetime(2008, 1, 1, 12, 30))
        assert not http.is_resource_modified(
            env, last_modified=datetime(2008, 1, 1, 12, 0)
        )
        assert http.is_resource_modified(env, last_modified=datetime(2008, 1, 1, 13, 0))

def test_is_resource_modified_for_range_requests(self):
        env = create_environ()
        env["HTTP_IF_MODIFIED_SINCE"] = http.http_date(datetime(2008, 1, 1, 12, 30))
        env["HTTP_IF_RANGE"] = http.generate_etag(b"awesome_if_range")
        assert not http.is_resource_modified(
            env,
            data=b"not_the_same",
            ignore_if_range=False,
            last_modified=datetime(2008, 1, 1, 12, 30),
        )
        env["HTTP_RANGE"] = ""
        assert not http.is_resource_modified(
            env, data=b"awesome_if_range", ignore_if_range=False
        )
        assert http.is_resource_modified(
            env, data=b"not_the_same", ignore_if_range=False
        )
        env["HTTP_IF_RANGE"] = http.http_date(datetime(2008, 1, 1, 13, 30))
        assert http.is_resource_modified(
            env, last_modified=datetime(2008, 1, 1, 14, 0), ignore_if_range=False
        )
        assert not http.is_resource_modified(
            env, last_modified=datetime(2008, 1, 1, 13, 30), ignore_if_range=False
        )
        assert http.is_resource_modified(
            env, last_modified=datetime(2008, 1, 1, 13, 30), ignore_if_range=True
        )

def test_etag_response_freezing():
    response = Response("Hello World")
    response.freeze()
    assert response.get_etag() == (str(generate_etag(b"Hello World")), False)