def test_response_decode_unicode(self):
        r = requests.Response()
        r._content_consumed = True
        r._content = b"the content"
        r.encoding = "ascii"
        chunks = r.iter_content(decode_unicode=True)
        assert all(isinstance(chunk, str) for chunk in chunks)
        r = requests.Response()
        r.raw = io.BytesIO(b"the content")
        r.encoding = "ascii"
        chunks = r.iter_content(decode_unicode=True)
        assert all(isinstance(chunk, str) for chunk in chunks)

def test_response_chunk_size_type(self):
        r = requests.Response()
        r.raw = io.BytesIO(b"the content")
        chunks = r.iter_content(1)
        assert all(len(chunk) == 1 for chunk in chunks)
        r = requests.Response()
        r.raw = io.BytesIO(b"the content")
        chunks = r.iter_content(None)
        assert list(chunks) == [b"the content"]
        r = requests.Response()
        r.raw = io.BytesIO(b"the content")
        with pytest.raises(TypeError):
            chunks = r.iter_content("1024")

@pytest.mark.parametrize(
        "exception, args, expected",
        (
            (urllib3.exceptions.ProtocolError, tuple(), ChunkedEncodingError),
            (urllib3.exceptions.DecodeError, tuple(), ContentDecodingError),
            (urllib3.exceptions.ReadTimeoutError, (None, "", ""), ConnectionError),
            (urllib3.exceptions.SSLError, tuple(), RequestsSSLError),
        ),
    )
    def test_iter_content_wraps_exceptions(self, httpbin, exception, args, expected):
        r = requests.Response()
        r.raw = mock.Mock()
        r.raw.stream.side_effect = exception(*args)
        with pytest.raises(expected):
            next(r.iter_content(1024))