def test_no_cache_conditional_default():
    rv = send_file(
        txt_path,
        EnvironBuilder(
            headers={"If-Modified-Since": http_date(datetime.datetime(2020, 7, 12))}
        ).get_environ(),
        last_modified=datetime.datetime(2020, 7, 11),
    )
    rv.close()
    assert "no-cache" in rv.headers["Cache-Control"]
    assert not rv.cache_control.public
    assert not rv.cache_control.max_age
    assert not rv.expires
    assert rv.status_code == 304

def test_remove_entity_headers(self):
        now = http.http_date()
        headers1 = [
            ("Date", now),
            ("Content-Type", "text/html"),
            ("Content-Length", "0"),
        ]
        headers2 = datastructures.Headers(headers1)
        http.remove_entity_headers(headers1)
        assert headers1 == [("Date", now)]
        http.remove_entity_headers(headers2)
        assert headers2 == datastructures.Headers([("Date", now)])

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

@pytest.mark.parametrize(
    ("value", "expect"),
    [
        (
            datetime(1994, 11, 6, 8, 49, 37, tzinfo=timezone.utc),
            "Sun, 06 Nov 1994 08:49:37 GMT",
        ),
        (
            datetime(1994, 11, 6, 8, 49, 37, tzinfo=timezone(timedelta(hours=-8))),
            "Sun, 06 Nov 1994 16:49:37 GMT",
        ),
        (datetime(1994, 11, 6, 8, 49, 37), "Sun, 06 Nov 1994 08:49:37 GMT"),
        (0, "Thu, 01 Jan 1970 00:00:00 GMT"),
        (datetime(1970, 1, 1), "Thu, 01 Jan 1970 00:00:00 GMT"),
        (datetime(1, 1, 1), "Mon, 01 Jan 0001 00:00:00 GMT"),
        (datetime(999, 1, 1), "Tue, 01 Jan 0999 00:00:00 GMT"),
        (datetime(1000, 1, 1), "Wed, 01 Jan 1000 00:00:00 GMT"),
        (datetime(2020, 1, 1), "Wed, 01 Jan 2020 00:00:00 GMT"),
        (date(2020, 1, 1), "Wed, 01 Jan 2020 00:00:00 GMT"),
    ],
)
def test_http_date(value, expect):
    assert http.http_date(value) == expect