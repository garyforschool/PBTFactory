def test_validate_attr_identifier__00(self):
        val = _validate_attr_identifier("foo", "line")
        self.assertEqual(val, "foo")

def test_validate_attr_identifier__01(self):
        for name in keyword.kwlist:
            with self.subTest(name=name):
                msg = f"""_validate_attr_identifier({name!r}, 'line')

A keyword has been passed in and expecting
an AttributeError to be raised.
"""
                with self.assertRaises(AttributeError, msg=msg):
                    _validate_attr_identifier(name, "line")

def test_validate_attr__identifier__02(self):
        for name in _BUILTIN_NAMES:
            with self.subTest(name=name):
                msg = f"""_validate_attr_identifier({name!r}, 'line')

A dunder builtin name has been passed in and
expecting an AttributeError to be raised.
"""
                with self.assertRaises(AttributeError, msg=msg):
                    _validate_attr_identifier(name, "line")

def test_validate_attr_identifier_dunders_error(self):
        for name in _DUNDERS:
            with self.subTest(name=name):
                msg = f"""_validate_attr_identifier({name!r}, 'line')

A special dunder name has been passed in and
expecting an AttributeError to be raised.
"""
                with self.assertRaises(AttributeError, msg=msg):
                    _validate_attr_identifier(name, "line")

def test_validate_attr_identifier__00(self) -> None:
        arg = ""
        line = ""
        exp = ""
        ret = _validate_attr_identifier(arg, line)
        self.assertEqual(
            ret,
            exp,
            msg=f"""

_validate_attr_identifier({arg!r}, {line!r})
expected: {exp!r}
     got: {ret!r}
""",
        )

def test_validate_attr_identifier__01(self) -> None:
        arg = "a_name"
        line = ""
        exp = "a_name"
        ret = _validate_attr_identifier(arg, line)
        self.assertEqual(
            ret,
            exp,
            msg=f"""

_validate_attr_identifier({arg!r}, {line!r})
expected: {exp!r}
     got: {ret!r}
""",
        )

def test_validate_attr_identifier__02(self) -> None:
        arg = "-arg"
        line = ""
        with self.assertRaises(AttributeError):
            _validate_attr_identifier(arg, line)

def test_validate_attr_identifier__03(self) -> None:
        patcher = patch("flutils.moduleutils.keyword.iskeyword", return_value=True)
        iskeyword = patcher.start()
        self.addCleanup(patcher.stop)
        with self.assertRaises(AttributeError):
            _validate_attr_identifier("try", "")
        iskeyword.assert_called_once_with("try")

def test_validate_attr_identifier__04(self) -> None:
        patcher = patch("flutils.moduleutils.keyword.iskeyword", return_value=False)
        iskeyword = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "flutils.moduleutils._BUILTIN_NAMES", new=["__a_builtin_name__"]
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        with self.assertRaises(AttributeError):
            _validate_attr_identifier("__a_builtin_name__", "")
        iskeyword.assert_called_once_with("__a_builtin_name__")

def test_validate_attr_identifier__05(self) -> None:
        patcher = patch("flutils.moduleutils.keyword.iskeyword", return_value=False)
        iskeyword = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "flutils.moduleutils._BUILTIN_NAMES", new=["__a_builtin_name__"]
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("flutils.moduleutils._DUNDERS", new=["__version__"])
        patcher.start()
        self.addCleanup(patcher.stop)
        with self.assertRaises(AttributeError):
            _validate_attr_identifier("__version__", "")
        iskeyword.assert_called_once_with("__version__")