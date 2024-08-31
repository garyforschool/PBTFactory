def test_chunked_upload():
    close_server = threading.Event()
    server = Server.basic_response_server(wait_to_close_event=close_server)
    data = iter([b"a", b"b", b"c"])
    with server as (host, port):
        url = f"http://{host}:{port}/"
        r = requests.post(url, data=data, stream=True)
        close_server.set()
    assert r.status_code == 200
    assert r.request.headers["Transfer-Encoding"] == "chunked"

def test_chunked_upload_uses_only_specified_host_header():
    close_server = threading.Event()
    server = Server(echo_response_handler, wait_to_close_event=close_server)
    data = iter([b"a", b"b", b"c"])
    custom_host = "sample-host"
    with server as (host, port):
        url = f"http://{host}:{port}/"
        r = requests.post(url, data=data, headers={"Host": custom_host}, stream=True)
        close_server.set()
    expected_header = b"Host: %s\r\n" % custom_host.encode("utf-8")
    assert expected_header in r.content
    assert r.content.count(b"Host: ") == 1

def test_chunked_upload_doesnt_skip_host_header():
    close_server = threading.Event()
    server = Server(echo_response_handler, wait_to_close_event=close_server)
    data = iter([b"a", b"b", b"c"])
    with server as (host, port):
        expected_host = f"{host}:{port}"
        url = f"http://{host}:{port}/"
        r = requests.post(url, data=data, stream=True)
        close_server.set()
    expected_header = b"Host: %s\r\n" % expected_host.encode("utf-8")
    assert expected_header in r.content
    assert r.content.count(b"Host: ") == 1

def test_HTTP_307_ALLOW_REDIRECT_POST(self, httpbin):
        r = requests.post(
            httpbin("redirect-to"),
            data="test",
            params={"url": "post", "status_code": 307},
        )
        assert r.status_code == 200
        assert r.history[0].status_code == 307
        assert r.history[0].is_redirect
        assert r.json()["data"] == "test"

def test_HTTP_307_ALLOW_REDIRECT_POST_WITH_SEEKABLE(self, httpbin):
        byte_str = b"test"
        r = requests.post(
            httpbin("redirect-to"),
            data=io.BytesIO(byte_str),
            params={"url": "post", "status_code": 307},
        )
        assert r.status_code == 200
        assert r.history[0].status_code == 307
        assert r.history[0].is_redirect
        assert r.json()["data"] == byte_str.decode("utf-8")

def test_http_301_changes_post_to_get(self, httpbin):
        r = requests.post(httpbin("status", "301"))
        assert r.status_code == 200
        assert r.request.method == "GET"
        assert r.history[0].status_code == 301
        assert r.history[0].is_redirect

def test_http_302_changes_post_to_get(self, httpbin):
        r = requests.post(httpbin("status", "302"))
        assert r.status_code == 200
        assert r.request.method == "GET"
        assert r.history[0].status_code == 302
        assert r.history[0].is_redirect

def test_http_303_changes_post_to_get(self, httpbin):
        r = requests.post(httpbin("status", "303"))
        assert r.status_code == 200
        assert r.request.method == "GET"
        assert r.history[0].status_code == 303
        assert r.history[0].is_redirect

def test_POSTBIN_GET_POST_FILES(self, httpbin):
        url = httpbin("post")
        requests.post(url).raise_for_status()
        post1 = requests.post(url, data={"some": "data"})
        assert post1.status_code == 200
        with open("requirements-dev.txt") as f:
            post2 = requests.post(url, files={"some": f})
        assert post2.status_code == 200
        post4 = requests.post(url, data='[{"some": "json"}]')
        assert post4.status_code == 200
        with pytest.raises(ValueError):
            requests.post(url, files=["bad file data"])

def test_invalid_files_input(self, httpbin):
        url = httpbin("post")
        post = requests.post(url, files={"random-file-1": None, "random-file-2": 1})
        assert b'name="random-file-1"' not in post.request.body
        assert b'name="random-file-2"' in post.request.body

def test_POSTBIN_SEEKED_OBJECT_WITH_NO_ITER(self, httpbin):

        class TestStream:

            def __init__(self, data):
                self.data = data.encode()
                self.length = len(self.data)
                self.index = 0

            def __len__(self):
                return self.length

            def read(self, size=None):
                if size:
                    ret = self.data[self.index : self.index + size]
                    self.index += size
                else:
                    ret = self.data[self.index :]
                    self.index = self.length
                return ret

            def tell(self):
                return self.index

            def seek(self, offset, where=0):
                if where == 0:
                    self.index = offset
                elif where == 1:
                    self.index += offset
                elif where == 2:
                    self.index = self.length + offset

        test = TestStream("test")
        post1 = requests.post(httpbin("post"), data=test)
        assert post1.status_code == 200
        assert post1.json()["data"] == "test"
        test = TestStream("test")
        test.seek(2)
        post2 = requests.post(httpbin("post"), data=test)
        assert post2.status_code == 200
        assert post2.json()["data"] == "st"

def test_POSTBIN_GET_POST_FILES_WITH_DATA(self, httpbin):
        url = httpbin("post")
        requests.post(url).raise_for_status()
        post1 = requests.post(url, data={"some": "data"})
        assert post1.status_code == 200
        with open("requirements-dev.txt") as f:
            post2 = requests.post(url, data={"some": "data"}, files={"some": f})
        assert post2.status_code == 200
        post4 = requests.post(url, data='[{"some": "json"}]')
        assert post4.status_code == 200
        with pytest.raises(ValueError):
            requests.post(url, files=["bad file data"])

def test_post_with_custom_mapping(self, httpbin):

        class CustomMapping(MutableMapping):

            def __init__(self, *args, **kwargs):
                self.data = dict(*args, **kwargs)

            def __delitem__(self, key):
                del self.data[key]

            def __getitem__(self, key):
                return self.data[key]

            def __setitem__(self, key, value):
                self.data[key] = value

            def __iter__(self):
                return iter(self.data)

            def __len__(self):
                return len(self.data)

        data = CustomMapping({"some": "data"})
        url = httpbin("post")
        found_json = requests.post(url, data=data).json().get("form")
        assert found_json == {"some": "data"}

def test_conflicting_post_params(self, httpbin):
        url = httpbin("post")
        with open("requirements-dev.txt") as f:
            with pytest.raises(ValueError):
                requests.post(url, data='[{"some": "data"}]', files={"some": f})

def test_different_encodings_dont_break_post(self, httpbin):
        with open(__file__, "rb") as f:
            r = requests.post(
                httpbin("post"),
                data={"stuff": json.dumps({"a": 123})},
                params={"blah": "asdf1234"},
                files={"file": ("test_requests.py", f)},
            )
        assert r.status_code == 200

@pytest.mark.parametrize(
        "data",
        (
            {"stuff": "ëlïxr"},
            {"stuff": "ëlïxr".encode()},
            {"stuff": "elixr"},
            {"stuff": b"elixr"},
        ),
    )
    def test_unicode_multipart_post(self, httpbin, data):
        with open(__file__, "rb") as f:
            r = requests.post(
                httpbin("post"), data=data, files={"file": ("test_requests.py", f)}
            )
        assert r.status_code == 200

def test_custom_content_type(self, httpbin):
        with open(__file__, "rb") as f1:
            with open(__file__, "rb") as f2:
                data = {"stuff": json.dumps({"a": 123})}
                files = {
                    "file1": ("test_requests.py", f1),
                    "file2": ("test_requests", f2, "text/py-content-type"),
                }
                r = requests.post(httpbin("post"), data=data, files=files)
        assert r.status_code == 200
        assert b"text/py-content-type" in r.request.body

def test_json_param_post_content_type_works(self, httpbin):
        r = requests.post(httpbin("post"), json={"life": 42})
        assert r.status_code == 200
        assert "application/json" in r.request.headers["Content-Type"]
        assert {"life": 42} == r.json()["json"]

def test_post_json_nan(self, httpbin):
        data = {"foo": float("nan")}
        with pytest.raises(requests.exceptions.InvalidJSONError):
            requests.post(httpbin("post"), json=data)