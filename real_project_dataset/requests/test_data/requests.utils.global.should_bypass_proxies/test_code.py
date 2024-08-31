@pytest.mark.parametrize(
    "url, expected",
    (
        ("http://192.168.0.1:5000/", True),
        ("http://192.168.0.1/", True),
        ("http://172.16.1.1/", True),
        ("http://172.16.1.1:5000/", True),
        ("http://localhost.localdomain:5000/v1.0/", True),
        ("http://google.com:6000/", True),
        ("http://172.16.1.12/", False),
        ("http://172.16.1.12:5000/", False),
        ("http://google.com:5000/v1.0/", False),
        ("file:///some/path/on/disk", True),
    ),
)
def test_should_bypass_proxies(url, expected, monkeypatch):
    monkeypatch.setenv(
        "no_proxy",
        "192.168.0.0/24,127.0.0.1,localhost.localdomain,172.16.1.1, google.com:6000",
    )
    monkeypatch.setenv(
        "NO_PROXY",
        "192.168.0.0/24,127.0.0.1,localhost.localdomain,172.16.1.1, google.com:6000",
    )
    assert should_bypass_proxies(url, no_proxy=None) == expected

@pytest.mark.parametrize(
    "url, expected",
    (
        ("http://172.16.1.1/", "172.16.1.1"),
        ("http://172.16.1.1:5000/", "172.16.1.1"),
        ("http://user:pass@172.16.1.1", "172.16.1.1"),
        ("http://user:pass@172.16.1.1:5000", "172.16.1.1"),
        ("http://hostname/", "hostname"),
        ("http://hostname:5000/", "hostname"),
        ("http://user:pass@hostname", "hostname"),
        ("http://user:pass@hostname:5000", "hostname"),
    ),
)
def test_should_bypass_proxies_pass_only_hostname(url, expected):
    with mock.patch("requests.utils.proxy_bypass") as proxy_bypass:
        should_bypass_proxies(url, no_proxy=None)
        proxy_bypass.assert_called_once_with(expected)

@pytest.mark.parametrize(
    "url, expected",
    (
        ("http://192.168.0.1:5000/", True),
        ("http://192.168.0.1/", True),
        ("http://172.16.1.1/", True),
        ("http://172.16.1.1:5000/", True),
        ("http://localhost.localdomain:5000/v1.0/", True),
        ("http://172.16.1.12/", False),
        ("http://172.16.1.12:5000/", False),
        ("http://google.com:5000/v1.0/", False),
    ),
)
def test_should_bypass_proxies_no_proxy(url, expected, monkeypatch):
    no_proxy = "192.168.0.0/24,127.0.0.1,localhost.localdomain,172.16.1.1"
    assert should_bypass_proxies(url, no_proxy=no_proxy) == expected

@pytest.mark.skipif(os.name != "nt", reason="Test only on Windows")
@pytest.mark.parametrize(
    "url, expected, override",
    (
        ("http://192.168.0.1:5000/", True, None),
        ("http://192.168.0.1/", True, None),
        ("http://172.16.1.1/", True, None),
        ("http://172.16.1.1:5000/", True, None),
        ("http://localhost.localdomain:5000/v1.0/", True, None),
        ("http://172.16.1.22/", False, None),
        ("http://172.16.1.22:5000/", False, None),
        ("http://google.com:5000/v1.0/", False, None),
        ("http://mylocalhostname:5000/v1.0/", True, "<local>"),
        ("http://192.168.0.1/", False, ""),
    ),
)
def test_should_bypass_proxies_win_registry(url, expected, override, monkeypatch):
    if override is None:
        override = "192.168.*;127.0.0.1;localhost.localdomain;172.16.1.1"
    import winreg

    class RegHandle:

        def Close(self):
            pass

    ie_settings = RegHandle()
    proxyEnableValues = deque([1, "1"])

    def OpenKey(key, subkey):
        return ie_settings

    def QueryValueEx(key, value_name):
        if key is ie_settings:
            if value_name == "ProxyEnable":
                proxyEnableValues.rotate()
                return [proxyEnableValues[0]]
            elif value_name == "ProxyOverride":
                return [override]

    monkeypatch.setenv("http_proxy", "")
    monkeypatch.setenv("https_proxy", "")
    monkeypatch.setenv("ftp_proxy", "")
    monkeypatch.setenv("no_proxy", "")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setattr(winreg, "OpenKey", OpenKey)
    monkeypatch.setattr(winreg, "QueryValueEx", QueryValueEx)
    assert should_bypass_proxies(url, None) == expected

@pytest.mark.skipif(os.name != "nt", reason="Test only on Windows")
def test_should_bypass_proxies_win_registry_bad_values(monkeypatch):
    import winreg

    class RegHandle:

        def Close(self):
            pass

    ie_settings = RegHandle()

    def OpenKey(key, subkey):
        return ie_settings

    def QueryValueEx(key, value_name):
        if key is ie_settings:
            if value_name == "ProxyEnable":
                return [""]
            elif value_name == "ProxyOverride":
                return ["192.168.*;127.0.0.1;localhost.localdomain;172.16.1.1"]

    monkeypatch.setenv("http_proxy", "")
    monkeypatch.setenv("https_proxy", "")
    monkeypatch.setenv("no_proxy", "")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setattr(winreg, "OpenKey", OpenKey)
    monkeypatch.setattr(winreg, "QueryValueEx", QueryValueEx)
    assert should_bypass_proxies("http://172.16.1.1/", None) is False

@pytest.mark.skipif(os.name != "nt", reason="Test only on Windows")
def test_should_bypass_proxies_win_registry_ProxyOverride_value(monkeypatch):
    import winreg

    class RegHandle:

        def Close(self):
            pass

    ie_settings = RegHandle()

    def OpenKey(key, subkey):
        return ie_settings

    def QueryValueEx(key, value_name):
        if key is ie_settings:
            if value_name == "ProxyEnable":
                return [1]
            elif value_name == "ProxyOverride":
                return [
                    "192.168.*;127.0.0.1;localhost.localdomain;172.16.1.1;<-loopback>;"
                ]

    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setenv("no_proxy", "")
    monkeypatch.setattr(winreg, "OpenKey", OpenKey)
    monkeypatch.setattr(winreg, "QueryValueEx", QueryValueEx)
    assert should_bypass_proxies("http://example.com/", None) is False