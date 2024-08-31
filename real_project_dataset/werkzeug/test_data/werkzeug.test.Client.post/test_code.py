def test_environ_builder_json():

    @Request.application
    def app(request):
        assert request.content_type == "application/json"
        return Response(json.loads(request.get_data(as_text=True))["foo"])

    c = Client(app)
    response = c.post("/", json={"foo": "bar"})
    assert response.text == "bar"
    with pytest.raises(TypeError):
        c.post("/", json={"foo": "bar"}, data={"baz": "qux"})

@pytest.mark.parametrize(
    ("code", "keep"), ((302, False), (301, False), (307, True), (308, True))
)
def test_follow_redirect_body(code, keep):

    @Request.application
    def app(request):
        if request.url == "http://localhost/some/redirect/":
            assert request.method == "POST" if keep else "GET"
            assert request.headers["X-Foo"] == "bar"
            if keep:
                assert request.form["foo"] == "bar"
            else:
                assert not request.form
            return Response(f"current url: {request.url}")
        return redirect("http://localhost/some/redirect/", code=code)

    c = Client(app)
    response = c.post(
        "/", follow_redirects=True, data={"foo": "bar"}, headers={"X-Foo": "bar"}
    )
    assert response.status_code == 200
    assert response.text == "current url: http://localhost/some/redirect/"

def test_multi_value_submit():
    c = Client(multi_value_post_app)
    data = {"field": ["val1", "val2"]}
    resp = c.post("/", data=data)
    assert resp.status_code == 200
    c = Client(multi_value_post_app)
    data = MultiDict({"field": ["val1", "val2"]})
    resp = c.post("/", data=data)
    assert resp.status_code == 200

def test_post_with_file_descriptor(tmpdir):
    c = Client(Response())
    f = tmpdir.join("some-file.txt")
    f.write("foo")
    with open(f.strpath) as data:
        resp = c.post("/", data=data)
    assert resp.status_code == 200
    with open(f.strpath, mode="rb") as data:
        resp = c.post("/", data=data)
    assert resp.status_code == 200

def test_base_request():
    client = Client(request_demo_app)
    response = client.get("/?foo=bar&foo=hehe")
    request = response.request
    assert request.args == MultiDict([("foo", "bar"), ("foo", "hehe")])
    assert request.form == MultiDict()
    assert request.data == b""
    assert_environ(request.environ, "GET")
    response = client.post(
        "/?blub=blah",
        data="foo=blub+hehe&blah=42",
        content_type="application/x-www-form-urlencoded",
    )
    request = response.request
    assert request.args == MultiDict([("blub", "blah")])
    assert request.form == MultiDict([("foo", "blub hehe"), ("blah", "42")])
    assert request.data == b""
    assert_environ(request.environ, "POST")
    response = client.patch(
        "/?blub=blah",
        data="foo=blub+hehe&blah=42",
        content_type="application/x-www-form-urlencoded",
    )
    request = response.request
    assert request.args == MultiDict([("blub", "blah")])
    assert request.form == MultiDict([("foo", "blub hehe"), ("blah", "42")])
    assert request.data == b""
    assert_environ(request.environ, "PATCH")
    json = b'{"foo": "bar", "blub": "blah"}'
    response = client.post("/?a=b", data=json, content_type="application/json")
    request = response.request
    assert request.data == json
    assert request.args == MultiDict([("a", "b")])
    assert request.form == MultiDict()

def test_basic(self):
        resources = join(dirname(__file__), "multipart")
        client = Client(form_data_consumer)
        repository = [
            (
                "firefox3-2png1txt",
                "---------------------------186454651713519341951581030105",
                [
                    ("anchor.png", "file1", "image/png", "file1.png"),
                    ("application_edit.png", "file2", "image/png", "file2.png"),
                ],
                "example text",
            ),
            (
                "firefox3-2pnglongtext",
                "---------------------------14904044739787191031754711748",
                [
                    ("accept.png", "file1", "image/png", "file1.png"),
                    ("add.png", "file2", "image/png", "file2.png"),
                ],
                "--long text\r\n--with boundary\r\n--lookalikes--",
            ),
            (
                "opera8-2png1txt",
                "----------zEO9jQKmLc2Cq88c23Dx19",
                [
                    ("arrow_branch.png", "file1", "image/png", "file1.png"),
                    ("award_star_bronze_1.png", "file2", "image/png", "file2.png"),
                ],
                "blafasel öäü",
            ),
            (
                "webkit3-2png1txt",
                "----WebKitFormBoundaryjdSFhcARk8fyGNy6",
                [
                    ("gtk-apply.png", "file1", "image/png", "file1.png"),
                    ("gtk-no.png", "file2", "image/png", "file2.png"),
                ],
                "this is another text with ümläüts",
            ),
            (
                "ie6-2png1txt",
                "---------------------------7d91b03a20128",
                [
                    ("file1.png", "file1", "image/x-png", "file1.png"),
                    ("file2.png", "file2", "image/x-png", "file2.png"),
                ],
                "ie6 sucks :-/",
            ),
        ]
        for name, boundary, files, text in repository:
            folder = join(resources, name)
            data = get_contents(join(folder, "request.http"))
            for filename, field, content_type, fsname in files:
                with client.post(
                    f"/?object={field}",
                    data=data,
                    content_type=f'multipart/form-data; boundary="{boundary}"',
                    content_length=len(data),
                ) as response:
                    lines = response.get_data().split(b"\n", 3)
                    assert lines[0] == repr(filename).encode("ascii")
                    assert lines[1] == repr(field).encode("ascii")
                    assert lines[2] == repr(content_type).encode("ascii")
                    assert lines[3] == get_contents(join(folder, fsname))
            with client.post(
                "/?object=text",
                data=data,
                content_type=f'multipart/form-data; boundary="{boundary}"',
                content_length=len(data),
            ) as response:
                assert response.get_data() == repr(text).encode()

@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
    def test_ie7_unc_path(self):
        client = Client(form_data_consumer)
        data_file = join(dirname(__file__), "multipart", "ie7_full_path_request.http")
        data = get_contents(data_file)
        boundary = "---------------------------7da36d1b4a0164"
        with client.post(
            "/?object=cb_file_upload_multiple",
            data=data,
            content_type=f'multipart/form-data; boundary="{boundary}"',
            content_length=len(data),
        ) as response:
            lines = response.get_data().split(b"\n", 3)
            assert lines[0] == b"'Sellersburg Town Council Meeting 02-22-2010doc.doc'"