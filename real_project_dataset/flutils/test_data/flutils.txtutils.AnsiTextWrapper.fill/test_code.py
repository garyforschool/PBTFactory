def test_width_40(self) -> None:
        exp = """Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum maximus
auctor. Cras a varius ligula. Phasellus
ut ipsum eu erat consequat posuere.
Pellentesque habitant morbi tristique
senectus et netus et malesuada fames ac
turpis egestas. Maecenas ultricies lacus
id massa interdum dignissim. Curabitur
efficitur ante sit amet nibh
consectetur, consequat rutrum nunc
egestas. Duis mattis arcu eget orci
euismod, sit amet vulputate ante
scelerisque. Aliquam ultrices, turpis id
gravida vestibulum, tortor ipsum
consequat mauris, eu cursus nisi felis
at felis. Quisque blandit lacus nec
mattis suscipit. Proin sed tortor ante.
Praesent fermentum orci id dolor
euismod, quis auctor nisl sodales."""
        arg = exp.replace("\n", " ")
        wrapper = AnsiTextWrapper(width=40)
        res = wrapper.fill(arg)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)

def test_width_44_with_indent(self) -> None:
        exp = """   Lorem ipsum dolor sit amet, consectetur
  adipiscing elit.Cras fermentum maximus
  auctor.Cras a varius ligula.Phasellus ut
  ipsum eu erat consequat posuere.
  Pellentesque habitant morbi tristique
  senectus et netus et malesuada fames ac
  turpis egestas.Maecenas ultricies lacus id
  massa interdum dignissim.Curabitur
  efficitur ante sit amet nibh consectetur,
  consequat rutrum nunc egestas.Duis mattis
  arcu eget orci euismod, sit amet vulputate
  ante scelerisque.Aliquam ultrices, turpis
  id gravida vestibulum, tortor ipsum
  consequat mauris, eu cursus nisi felis at
  felis.Quisque blandit lacus nec mattis
  suscipit.Proin sed tortor ante.Praesent
  fermentum orci id dolor euismod, quis
  auctor nisl sodales."""
        arg = "\n".join(map(lambda x: x.lstrip(), exp.splitlines()))
        arg = arg.replace("\n", " ")
        wrapper = AnsiTextWrapper(
            width=44, initial_indent="   ", subsequent_indent="  "
        )
        res = wrapper.fill(arg)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)

def test_width_0_raises(self) -> None:
        with self.assertRaises(ValueError):
            wrapper = AnsiTextWrapper(width=0)
            wrapper.fill("foo bar foo bar")

def test_width_3_with_indent_raises(self) -> None:
        with self.assertRaises(ValueError):
            wrapper = AnsiTextWrapper(width=3, initial_indent=" " * 10, max_lines=1)
            wrapper.fill("foo bar foo bar")

def test_max_lines_of_5(self) -> None:
        exp = """Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum maximus
auctor. Cras a varius ligula. Phasellus
ut ipsum eu erat consequat posuere.
Pellentesque habitant morbi tristique"""
        arg = exp.replace("\n", " ")
        wrapper = AnsiTextWrapper(width=40, max_lines=5)
        res = wrapper.fill(arg)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)

def test_max_lines_of_3_with_placeholder(self) -> None:
        text = """Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum maximus
auctor. Cras a varius ligula. Phasellus
ut ipsum eu erat consequat posuere.
Pellentesque habitant morbi tristique
senectus et netus et malesuada fames ac
turpis egestas. Maecenas ultricies lacus
id massa interdum dignissim. Curabitur
efficitur ante sit amet nibh
consectetur, consequat rutrum nunc
egestas. Duis mattis arcu eget orci
euismod, sit amet vulputate ante
scelerisque. Aliquam ultrices, turpis id
gravida vestibulum, tortor ipsum
consequat mauris, eu cursus nisi felis
at felis. Quisque blandit lacus nec
mattis suscipit. Proin sed tortor ante.
Praesent fermentum orci id dolor
euismod, quis auctor nisl sodales."""
        arg = text.replace("\n", " ")
        exp = """Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum maximus
.................................."""
        wrapper = AnsiTextWrapper(width=40, max_lines=3, placeholder="." * 34)
        res = wrapper.fill(arg)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)

def test_max_lines_of_3_placeholder_with_long_word(self) -> None:
        text = """Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum
1234567890123456789012345678901234567890
senectus et netus et malesuada fames ac"""
        arg = text.replace("\n", " ")
        exp = "Lorem ipsum dolor sit amet, consectetur\nadipiscing elit. Cras fermentum [...]"
        wrapper = AnsiTextWrapper(width=40, max_lines=3)
        res = wrapper.fill(arg)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)

def test_max_lines_of_five_with_placeholder(self) -> None:
        text = """Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum maximus
auctor. Cras a varius ligula. Phasellus
ut ipsum eu erat consequat posuere.
Pellentesque habitant morbi tristique
senectus et netus et malesuada fames ac
turpis egestas. Maecenas ultricies lacus
id massa interdum dignissim. Curabitur
efficitur ante sit amet nibh
consectetur, consequat rutrum nunc
egestas. Duis mattis arcu eget orci
euismod, sit amet vulputate ante
scelerisque. Aliquam ultrices, turpis id
gravida vestibulum, tortor ipsum
consequat mauris, eu cursus nisi felis
at felis. Quisque blandit lacus nec
mattis suscipit. Proin sed tortor ante.
Praesent fermentum orci id dolor
euismod, quis auctor nisl sodales."""
        arg = text.replace("\n", " ")
        exp = """Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum maximus
auctor. Cras a varius ligula. Phasellus
ut ipsum eu erat consequat posuere.
Pellentesque habitant morbi [...]"""
        wrapper = AnsiTextWrapper(width=40, max_lines=5)
        res = wrapper.fill(arg)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)

def test_large_word(self) -> None:
        arg = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras fermentum maximus auctor. Cras a varius ligula. Phasellus ut ipsum eu erat consequat posuere. Duis Pellentesquehabitantmorbitristiquesenectusetnetusetmalesuadafamesacblandit turpis egestas. Maecenas ultricies lacus id massa interdum dignissim. Curabitur efficitur ante sit amet nibh consectetur, consequat rutrum nunc egestas. Duis mattis arcu eget orci euismod, sit amet vulputate ante scelerisque. Aliquam ultrices, turpis id gravida vestibulum, tortor ipsum consequat mauris, eu cursus nisi felis at felis. Quisque blandit lacus nec mattis suscipit. Proin sed tortor ante. Praesent fermentum orci id dolor euismod, quis auctor nisl sodales."
        exp = """Lorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum maximus
auctor. Cras a varius ligula. Phasellus
ut ipsum eu erat consequat posuere. Duis
Pellentesquehabitantmorbitristiquesenect
usetnetusetmalesuadafamesacblandit
turpis egestas. Maecenas ultricies lacus
id massa interdum dignissim. Curabitur
efficitur ante sit amet nibh
consectetur, consequat rutrum nunc
egestas. Duis mattis arcu eget orci
euismod, sit amet vulputate ante
scelerisque. Aliquam ultrices, turpis id
gravida vestibulum, tortor ipsum
consequat mauris, eu cursus nisi felis
at felis. Quisque blandit lacus nec
mattis suscipit. Proin sed tortor ante.
Praesent fermentum orci id dolor
euismod, quis auctor nisl sodales."""
        wrapper = AnsiTextWrapper(width=40)
        res = wrapper.fill(arg)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)

def test_width_40_ansi_all(self) -> None:
        exp = """[31mLorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum maximus
auctor. Cras a varius ligula. Phasellus
ut ipsum eu erat consequat posuere.
Pellentesque habitant morbi tristique
senectus et netus et malesuada fames ac
turpis egestas. Maecenas ultricies lacus
id massa interdum dignissim. Curabitur
efficitur ante sit amet nibh
consectetur, consequat rutrum nunc
egestas. Duis mattis arcu eget orci
euismod, sit amet vulputate ante
scelerisque. Aliquam ultrices, turpis id
gravida vestibulum, tortor ipsum
consequat mauris, eu cursus nisi felis
at felis. Quisque blandit lacus nec
mattis suscipit. Proin sed tortor ante.
Praesent fermentum orci id dolor
euismod, quis auctor nisl sodales.[0m"""
        arg = exp.replace("\n", " ")
        wrapper = AnsiTextWrapper(width=40)
        res = wrapper.fill(arg)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)

def test_width_40_ansi_mixed(self) -> None:
        exp = """[31m[1m[4mLorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum maximus
auctor. Cras a varius ligula. Phasellus
ut ipsum eu erat consequat posuere.[0m
Pellentesque habitant morbi tristique
senectus et netus et malesuada fames ac
turpis egestas. Maecenas ultricies lacus
id massa interdum dignissim. Curabitur[38;2;55;172;230m
efficitur ante sit amet nibh
consectetur, consequat rutrum nunc[0m
egestas. Duis mattis arcu eget orci
euismod, sit amet vulputate ante
scelerisque. Aliquam ultrices, turpis id
gravida vestibulum, tortor ipsum
consequat mauris, eu cursus nisi felis
at felis. Quisque blandit lacus nec
mattis suscipit. Proin sed tortor ante.
Praesent fermentum orci id dolor[38;5;208m
euismod, quis auctor nisl sodales.[0m"""
        arg = exp.replace("\n", " ")
        wrapper = AnsiTextWrapper(width=40)
        res = wrapper.fill(arg)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)

def test_width_40_indent_ansi_mixed(self) -> None:
        text = """[31m[1m[4mLorem ipsum dolor sit amet, consectetur
adipiscing elit. Cras fermentum maximus
auctor. Cras a varius ligula. Phasellus
ut ipsum eu erat consequat posuere.[0m
Pellentesque habitant morbi tristique
senectus et netus et malesuada fames ac
turpis egestas. Maecenas ultricies lacus
id massa interdum dignissim. Curabitur[38;2;55;172;230m
efficitur ante sit amet nibh
consectetur, consequat rutrum nunc[0m
egestas. Duis mattis arcu eget orci
euismod, sit amet vulputate ante
scelerisque. Aliquam ultrices, turpis id
gravida vestibulum, tortor ipsum
consequat mauris, eu cursus nisi felis
at felis. Quisque blandit lacus nec
mattis suscipit. Proin sed tortor ante.
Praesent fermentum orci id dolor[38;5;208m
euismod, quis auctor nisl sodales.[0m"""
        initial_indent = "\x1b[47m\x1b[30m...\x1b[0m"
        exp = """[47m[30m...[0m[31m[1m[4mLorem ipsum dolor sit amet,
[47m[30m...[0mconsectetur adipiscing elit. Cras
[47m[30m...[0mfermentum maximus auctor. Cras a
[47m[30m...[0mvarius ligula. Phasellus ut ipsum eu
[47m[30m...[0merat consequat posuere.[0m Pellentesque
[47m[30m...[0mhabitant morbi tristique senectus et
[47m[30m...[0mnetus et malesuada fames ac turpis
[47m[30m...[0megestas. Maecenas ultricies lacus id
[47m[30m...[0mmassa interdum dignissim. Curabitur[38;2;55;172;230m
[47m[30m...[0mefficitur ante sit amet nibh
[47m[30m...[0mconsectetur, consequat rutrum nunc[0m
[47m[30m...[0megestas. Duis mattis arcu eget orci
[47m[30m...[0meuismod, sit amet vulputate ante
[47m[30m...[0mscelerisque. Aliquam ultrices, turpis
[47m[30m...[0mid gravida vestibulum, tortor ipsum
[47m[30m...[0mconsequat mauris, eu cursus nisi
[47m[30m...[0mfelis at felis. Quisque blandit lacus
[47m[30m...[0mnec mattis suscipit. Proin sed tortor
[47m[30m...[0mante. Praesent fermentum orci id
[47m[30m...[0mdolor[38;5;208m euismod, quis auctor nisl
[47m[30m...[0msodales.[0m"""
        arg = text.replace("\n", " ")
        wrapper = AnsiTextWrapper(
            width=40, initial_indent=initial_indent, subsequent_indent=initial_indent
        )
        res = wrapper.fill(arg)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)