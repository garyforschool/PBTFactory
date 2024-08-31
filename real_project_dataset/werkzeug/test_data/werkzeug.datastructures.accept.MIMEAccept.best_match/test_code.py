@pytest.mark.parametrize(
        ("values", "matches", "default", "expect"),
        [
            ([("text/*", 1)], ["text/html"], None, "text/html"),
            ([("text/*", 1)], ["image/png"], "text/plain", "text/plain"),
            ([("text/*", 1)], ["image/png"], None, None),
            (
                [("*/*", 1), ("text/html", 1)],
                ["image/png", "text/html"],
                None,
                "text/html",
            ),
            (
                [("*/*", 1), ("text/html", 1)],
                ["image/png", "text/plain"],
                None,
                "image/png",
            ),
            (
                [("*/*", 1), ("text/html", 1), ("image/*", 1)],
                ["image/png", "text/html"],
                None,
                "text/html",
            ),
            (
                [("*/*", 1), ("text/html", 1), ("image/*", 1)],
                ["text/plain", "image/png"],
                None,
                "image/png",
            ),
            (
                [("text/html", 1), ("text/html; level=1", 1)],
                ["text/html;level=1"],
                None,
                "text/html;level=1",
            ),
        ],
    )
    def test_mime_accept(self, values, matches, default, expect):
        accept = ds.MIMEAccept(values)
        match = accept.best_match(matches, default=default)
        assert match == expect