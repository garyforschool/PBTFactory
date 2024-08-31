def test_rewind_body(self):
        data = io.BytesIO(b"the data")
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position == 0
        assert prep.body.read() == b"the data"
        assert prep.body.read() == b""
        requests.utils.rewind_body(prep)
        assert prep.body.read() == b"the data"

def test_rewind_partially_read_body(self):
        data = io.BytesIO(b"the data")
        data.read(4)
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position == 4
        assert prep.body.read() == b"data"
        assert prep.body.read() == b""
        requests.utils.rewind_body(prep)
        assert prep.body.read() == b"data"

def test_rewind_body_no_seek(self):

        class BadFileObj:

            def __init__(self, data):
                self.data = data

            def tell(self):
                return 0

            def __iter__(self):
                return

        data = BadFileObj("the data")
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position == 0
        with pytest.raises(UnrewindableBodyError) as e:
            requests.utils.rewind_body(prep)
        assert "Unable to rewind request body" in str(e)

def test_rewind_body_failed_seek(self):

        class BadFileObj:

            def __init__(self, data):
                self.data = data

            def tell(self):
                return 0

            def seek(self, pos, whence=0):
                raise OSError()

            def __iter__(self):
                return

        data = BadFileObj("the data")
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position == 0
        with pytest.raises(UnrewindableBodyError) as e:
            requests.utils.rewind_body(prep)
        assert "error occurred when rewinding request body" in str(e)

def test_rewind_body_failed_tell(self):

        class BadFileObj:

            def __init__(self, data):
                self.data = data

            def tell(self):
                raise OSError()

            def __iter__(self):
                return

        data = BadFileObj("the data")
        prep = requests.Request("GET", "http://example.com", data=data).prepare()
        assert prep._body_position is not None
        with pytest.raises(UnrewindableBodyError) as e:
            requests.utils.rewind_body(prep)
        assert "Unable to rewind request body" in str(e)