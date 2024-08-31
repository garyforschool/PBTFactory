def test_parse_from_environ(self):
        parser = FormDataParser()
        stream, _, _ = parser.parse_from_environ({"wsgi.input": ""})
        assert stream is not None