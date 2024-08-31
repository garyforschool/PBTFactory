@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
@pytest.mark.dev_server
def test_ssl_dev_cert(tmp_path, dev_server):
    client = dev_server(ssl_context=make_ssl_devcert(tmp_path))
    r = client.request()
    assert r.json["wsgi.url_scheme"] == "https"