@pytest.mark.parametrize(
        ("value", "expect"),
        [(None, ""), ("", ""), (";a=b", ""), ("v", "v"), ("v;", "v")],
    )
    def test_parse_options_header_empty(self, value, expect):
        assert http.parse_options_header(value) == (expect, {})

@pytest.mark.parametrize(
        ("value", "expect"),
        [
            ("v;a=b;c=d;", {"a": "b", "c": "d"}),
            ("v;  ; a=b ; ", {"a": "b"}),
            ("v;a", {}),
            ("v;a=", {}),
            ("v;=b", {}),
            ('v;a="b"', {"a": "b"}),
            ("v;a=µ", {}),
            ('v;a="\';\'";b="µ";', {"a": "';'", "b": "µ"}),
            ('v;a="b c"', {"a": "b c"}),
            ('v;a="b\\"c";d=e', {"a": 'b"c', "d": "e"}),
            ('v;a="c:\\\\"', {"a": "c:\\"}),
            ('v;a="c:\\"', {"a": "c:\\"}),
            ('v;a="b\\\\\\"c"', {"a": 'b\\"c'}),
            ('v;a="b%22c"', {"a": 'b"c'}),
            ("v;a*=b", {"a": "b"}),
            ("v;a*=ASCII'en'b", {"a": "b"}),
            ("v;a*=US-ASCII''%62", {"a": "b"}),
            ("v;a*=UTF-8''%C2%B5", {"a": "µ"}),
            ("v;a*=US-ASCII''%C2%B5", {"a": "��"}),
            ("v;a*=BAD''%62", {"a": "%62"}),
            ("v;a*=UTF-8'''%F0%9F%90%8D'.txt", {"a": "'🐍'.txt"}),
            ('v;a="🐍.txt"', {"a": "🐍.txt"}),
            ("v;a*0=b;a*1=c;d=e", {"a": "bc", "d": "e"}),
            ("v;a*0*=b", {"a": "b"}),
            ("v;a*0*=UTF-8''b;a*1=c;a*2*=%C2%B5", {"a": "bcµ"}),
        ],
    )
    def test_parse_options_header(self, value, expect) -> None:
        assert http.parse_options_header(value) == ("v", expect)

def test_parse_options_header_broken_values(self):
        assert http.parse_options_header(" ") == ("", {})
        assert http.parse_options_header(" , ") == (",", {})
        assert http.parse_options_header(" ; ") == ("", {})
        assert http.parse_options_header(" ,; ") == (",", {})
        assert http.parse_options_header(" , a ") == (", a", {})
        assert http.parse_options_header(" ; a ") == ("", {})

def test_parse_options_header_case_insensitive(self):
        _, options = http.parse_options_header('something; fileName="File.ext"')
        assert options["filename"] == "File.ext"