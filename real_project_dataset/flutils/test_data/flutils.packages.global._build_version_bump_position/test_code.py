def test_build_version_bump_position__1(self) -> None:
        exp = 2
        position = 2
        ret = _build_version_bump_position(position)
        self.assertEqual(
            ret,
            exp,
            msg="""

_build_version_bump_position({position!r})

expected:

{exp!r}

got:

{ret!r}

""".format(
                position=position, exp=exp, ret=ret
            ),
        )

def test_build_version_bump_position__2(self) -> None:
        exp = 0
        position = -3
        ret = _build_version_bump_position(position)
        self.assertEqual(
            ret,
            exp,
            msg="""

_build_version_bump_position({position!r})

expected:

{exp!r}

got:

{ret!r}

""".format(
                position=position, exp=exp, ret=ret
            ),
        )

def test_build_version_bump_position__3(self) -> None:
        exp = 2
        position = -1
        ret = _build_version_bump_position(position)
        self.assertEqual(
            ret,
            exp,
            msg="""

_build_version_bump_position({position!r})

expected:

{exp!r}

got:

{ret!r}

""".format(
                position=position, exp=exp, ret=ret
            ),
        )

def test_build_version_bump_position__4(self) -> None:
        position = 3
        with self.assertRaises(ValueError):
            _build_version_bump_position(position)

def test_build_version_bump_position__5(self) -> None:
        position = -4
        with self.assertRaises(ValueError):
            _build_version_bump_position(position)