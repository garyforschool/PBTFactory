@pytest.mark.parametrize(
    "cookiejar", (compat.cookielib.CookieJar(), RequestsCookieJar())
)
def test_add_dict_to_cookiejar(cookiejar):
    cookiedict = {"test": "cookies", "good": "cookies"}
    cj = add_dict_to_cookiejar(cookiejar, cookiedict)
    cookies = {cookie.name: cookie.value for cookie in cj}
    assert cookiedict == cookies