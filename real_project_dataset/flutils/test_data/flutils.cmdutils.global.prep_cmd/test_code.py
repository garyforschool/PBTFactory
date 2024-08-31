def test_bytes(self) -> None:
        arg = b"ls -flap"
        exp = tuple(shlex.split(arg.decode("utf-8")))
        got = prep_cmd(arg)
        msg = f"\n\nflutils.cmdutils.prep_cmd({arg!r})\n\nexp = {exp!r}got = {got!r}"
        self.assertEqual(got, exp, msg=msg)

def test_str(self) -> None:
        arg = "ls -flap"
        exp = tuple(shlex.split(arg))
        got = prep_cmd(arg)
        msg = f"\n\nflutils.cmdutils.prep_cmd({arg!r})\n\nexp = {exp!r}got = {got!r}"
        self.assertEqual(got, exp, msg=msg)

def test_list(self) -> None:
        arg = ["ls", "-flap"]
        exp = tuple(arg)
        got = prep_cmd(arg)
        msg = f"\n\nflutils.cmdutils.prep_cmd({arg!r})\n\nexp = {exp!r}got = {got!r}"
        self.assertEqual(got, exp, msg=msg)

def test_tuple(self) -> None:
        arg = "ls", "-flap"
        exp = tuple(arg)
        got = prep_cmd(arg)
        msg = f"\n\nflutils.cmdutils.prep_cmd({arg!r})\n\nexp = {exp!r}got = {got!r}"
        self.assertEqual(got, exp, msg=msg)

def test_non_sequence_raises(self) -> None:
        with self.assertRaises(TypeError):
            prep_cmd(1)
        with self.assertRaises(TypeError):
            prep_cmd(None)

def test_non_str_item(self) -> None:
        with self.assertRaises(TypeError):
            prep_cmd(["ls", 1])