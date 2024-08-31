def test_list_with_ansi(self) -> None:
        chunks = ["foo", " ", "\x1b[31m", "bar", "\x1b[0m"]
        res = len_without_ansi(chunks)
        self.assertEqual(res, 7)

def test_list_without_ansi(self) -> None:
        chunks = ["foo"]
        res = len_without_ansi(chunks)
        self.assertEqual(res, 3)

def test_string_with_ansi(self) -> None:
        chunks = "\x1b[38;5;209mfoobar\x1b[0m"
        res = len_without_ansi(chunks)
        self.assertEqual(res, 6)

def test_string_without_ansi(self) -> None:
        chunks = "foo bar"
        res = len_without_ansi(chunks)
        self.assertEqual(res, 7)