def test_parse_bad_content_type(self):
        parser = FormDataParser()
        assert parser.parse("", "bad-mime-type", 0) == (
            "",
            MultiDict([]),
            MultiDict([]),
        )