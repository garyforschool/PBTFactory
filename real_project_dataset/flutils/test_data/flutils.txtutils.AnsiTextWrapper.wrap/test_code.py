def test_width_40_indent_ansi_mixed_placeholder(self) -> None:
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
[47m[30m...[0merat consequat posuere.[0m [31m[...][0m"""
        arg = text.replace("\n", " ")
        wrapper = AnsiTextWrapper(
            width=40,
            initial_indent=initial_indent,
            subsequent_indent=initial_indent,
            max_lines=5,
            placeholder=" \x1b[31m[...]\x1b[0m",
        )
        res = wrapper.wrap(arg)
        res = "\n".join(res)
        msg = _build_msg(exp, res)
        self.assertEqual(exp, res, msg=msg)