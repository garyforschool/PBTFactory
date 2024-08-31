def test_none(self):
        encodings = get_encodings_from_content("")
        assert not len(encodings)

@pytest.mark.parametrize(
        "content",
        (
            '<meta charset="UTF-8">',
            '<meta http-equiv="Content-type" content="text/html;charset=UTF-8">',
            '<meta http-equiv="Content-type" content="text/html;charset=UTF-8" />',
            '<?xml version="1.0" encoding="UTF-8"?>',
        ),
    )
    def test_pragmas(self, content):
        encodings = get_encodings_from_content(content)
        assert len(encodings) == 1
        assert encodings[0] == "UTF-8"

def test_precedence(self):
        content = """
        <?xml version="1.0" encoding="XML"?>
        <meta charset="HTML5">
        <meta http-equiv="Content-type" content="text/html;charset=HTML4" />
        """.strip()
        assert get_encodings_from_content(content) == ["HTML5", "HTML4", "XML"]