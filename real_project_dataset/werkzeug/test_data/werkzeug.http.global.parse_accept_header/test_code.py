def test_accept(self):
        a = http.parse_accept_header("en-us,ru;q=0.5")
        assert list(a.values()) == ["en-us", "ru"]
        assert a.best == "en-us"
        assert a.find("ru") == 1
        pytest.raises(ValueError, a.index, "de")
        assert a.to_header() == "en-us,ru;q=0.5"

def test_accept_parameter_with_space(self):
        a = http.parse_accept_header('application/x-special; z="a b";q=0.5')
        assert a['application/x-special; z="a b"'] == 0.5

def test_mime_accept(self):
        a = http.parse_accept_header(
            "text/xml,application/xml,application/xhtml+xml,application/foo;quiet=no; bar=baz;q=0.6,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
            datastructures.MIMEAccept,
        )
        pytest.raises(ValueError, lambda: a["missing"])
        assert a["image/png"] == 1
        assert a["text/plain"] == 0.8
        assert a["foo/bar"] == 0.5
        assert a["application/foo;quiet=no; bar=baz"] == 0.6
        assert a[a.find("foo/bar")] == ("*/*", 0.5)

def test_accept_matches(self):
        a = http.parse_accept_header(
            "text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png",
            datastructures.MIMEAccept,
        )
        assert (
            a.best_match(["text/html", "application/xhtml+xml"])
            == "application/xhtml+xml"
        )
        assert a.best_match(["text/html"]) == "text/html"
        assert a.best_match(["foo/bar"]) is None
        assert a.best_match(["foo/bar", "bar/foo"], default="foo/bar") == "foo/bar"
        assert a.best_match(["application/xml", "text/xml"]) == "application/xml"

def test_accept_mime_specificity(self):
        a = http.parse_accept_header(
            "text/*, text/html, text/html;level=1, */*", datastructures.MIMEAccept
        )
        assert a.best_match(["text/html; version=1", "text/html"]) == "text/html"
        assert a.best_match(["text/html", "text/html; level=1"]) == "text/html; level=1"

def test_charset_accept(self):
        a = http.parse_accept_header(
            "ISO-8859-1,utf-8;q=0.7,*;q=0.7", datastructures.CharsetAccept
        )
        assert a["iso-8859-1"] == a["iso8859-1"]
        assert a["iso-8859-1"] == 1
        assert a["UTF8"] == 0.7
        assert a["ebcdic"] == 0.7

def test_language_accept(self):
        a = http.parse_accept_header(
            "de-AT,de;q=0.8,en;q=0.5", datastructures.LanguageAccept
        )
        assert a.best == "de-AT"
        assert "de_AT" in a
        assert "en" in a
        assert a["de-at"] == 1
        assert a["en"] == 0.5

def test_best_match_works(self):
        rv = http.parse_accept_header(
            "foo=,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
            datastructures.MIMEAccept,
        ).best_match(["foo/bar"])
        assert rv == "foo/bar"

@pytest.mark.parametrize("value", [".5", "+0.5", "0.5_1", "🯰.🯵"])
def test_accept_invalid_float(value):
    quoted = urllib.parse.quote(value)
    if quoted == value:
        q = f"q={value}"
    else:
        q = f"q*=UTF-8''{value}"
    a = http.parse_accept_header(f"en,jp;{q}")
    assert list(a.values()) == ["en"]

def test_accept_valid_int_one_zero():
    assert http.parse_accept_header("en;q=1") == http.parse_accept_header("en;q=1.0")
    assert http.parse_accept_header("en;q=0") == http.parse_accept_header("en;q=0.0")
    assert http.parse_accept_header("en;q=5") == http.parse_accept_header("en;q=5.0")