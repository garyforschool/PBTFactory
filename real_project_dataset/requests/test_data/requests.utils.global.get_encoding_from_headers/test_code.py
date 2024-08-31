@pytest.mark.parametrize(
    "value, expected",
    (
        (CaseInsensitiveDict(), None),
        (
            CaseInsensitiveDict({"content-type": "application/json; charset=utf-8"}),
            "utf-8",
        ),
        (CaseInsensitiveDict({"content-type": "text/plain"}), "ISO-8859-1"),
    ),
)
def test_get_encoding_from_headers(value, expected):
    assert get_encoding_from_headers(value) == expected