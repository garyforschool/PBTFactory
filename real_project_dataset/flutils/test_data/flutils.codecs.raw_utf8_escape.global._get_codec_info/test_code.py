def test_get_codec_info(self) -> None:
        val = _get_codec_info("foo")
        self.assertEqual(val, None)