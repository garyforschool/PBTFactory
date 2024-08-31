@pytest.mark.parametrize(
    "uri, expected",
    (
        (
            "http://example.com/fiz?buz=%25ppicture",
            "http://example.com/fiz?buz=%25ppicture",
        ),
        (
            "http://example.com/fiz?buz=%ppicture",
            "http://example.com/fiz?buz=%25ppicture",
        ),
    ),
)
def test_requote_uri_with_unquoted_percents(uri, expected):
    assert requote_uri(uri) == expected