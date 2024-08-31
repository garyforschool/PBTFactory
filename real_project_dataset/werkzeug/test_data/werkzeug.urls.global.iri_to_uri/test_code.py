def test_iri_support():
    assert urls.uri_to_iri("http://xn--n3h.net/") == "http://☃.net/"
    assert urls.iri_to_uri("http://☃.net/") == "http://xn--n3h.net/"
    assert (
        urls.iri_to_uri("http://üser:pässword@☃.net/påth")
        == "http://%C3%BCser:p%C3%A4ssword@xn--n3h.net/p%C3%A5th"
    )
    assert (
        urls.uri_to_iri("http://test.com/%3Fmeh?foo=%26%2F")
        == "http://test.com/%3Fmeh?foo=%26/"
    )
    assert urls.iri_to_uri("/foo") == "/foo"
    assert (
        urls.iri_to_uri("http://föö.com:8080/bam/baz")
        == "http://xn--f-1gaa.com:8080/bam/baz"
    )

def test_iri_safe_quoting():
    uri = "http://xn--f-1gaa.com/%2F%25?q=%C3%B6&x=%3D%25#%25"
    iri = "http://föö.com/%2F%25?q=ö&x=%3D%25#%25"
    assert urls.uri_to_iri(uri) == iri
    assert urls.iri_to_uri(urls.uri_to_iri(uri)) == uri

def test_quoting_of_local_urls():
    rv = urls.iri_to_uri("/foo\x8f")
    assert rv == "/foo%C2%8F"

def test_iri_to_uri_idempotence_ascii_only():
    uri = "http://www.idempoten.ce"
    uri = urls.iri_to_uri(uri)
    assert urls.iri_to_uri(uri) == uri

def test_iri_to_uri_idempotence_non_ascii():
    uri = "http://☃/☃"
    uri = urls.iri_to_uri(uri)
    assert urls.iri_to_uri(uri) == uri

def test_iri_to_uri_to_iri():
    iri = "http://föö.com/"
    uri = urls.iri_to_uri(iri)
    assert urls.uri_to_iri(uri) == iri

def test_uri_to_iri_to_uri():
    uri = "http://xn--f-rgao.com/%C3%9E"
    iri = urls.uri_to_iri(uri)
    assert urls.iri_to_uri(iri) == uri

@pytest.mark.parametrize(
    "value",
    [
        "http://föñ.com/☐/fred?utf8=✓",
        "http://xn--f-rgao.com/☐/fred?utf8=✓",
        "http://xn--f-rgao.com/%E2%98%90/fred?utf8=%E2%9C%93",
        "http://xn--f-rgao.com/%E2%98%90/fred?utf8=%E2%9C%93",
        "http://föñ.com/☐/fred?utf8=%E2%9C%93",
    ],
)
def test_uri_iri_normalization(value):
    uri = "http://xn--f-rgao.com/%E2%98%90/fred?utf8=%E2%9C%93"
    iri = "http://föñ.com/☐/fred?utf8=✓"
    assert urls.uri_to_iri(value) == iri
    assert urls.iri_to_uri(value) == uri
    assert urls.uri_to_iri(urls.iri_to_uri(value)) == iri
    assert urls.iri_to_uri(urls.uri_to_iri(value)) == uri
    assert urls.uri_to_iri(urls.uri_to_iri(value)) == iri
    assert urls.iri_to_uri(urls.iri_to_uri(value)) == uri

def test_iri_to_uri_dont_quote_valid_code_points():
    assert urls.iri_to_uri("/path[bracket]?(paren)") == "/path%5Bbracket%5D?(paren)"

def test_itms_services() -> None:
    url = "itms-services://?action=download-manifest&url=https://test.example/path"
    assert urls.iri_to_uri(url) == url