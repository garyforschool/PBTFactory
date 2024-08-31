    def test_added_tab_hint(self):
        # Check fix for bug #1488943
        diff = list(difflib.Differ().compare(["\tI am a buggy"],["\t\tI am a bug"]))
        self.assertEqual("- \tI am a buggy", diff[0])
        self.assertEqual("? \t          --\n", diff[1])
        self.assertEqual("+ \t\tI am a bug", diff[2])
        self.assertEqual("? +\n", diff[3])

    def test_hint_indented_properly_with_tabs(self):
        diff = list(difflib.Differ().compare(["\t \t \t^"], ["\t \t \t^\n"]))
        self.assertEqual("- \t \t \t^", diff[0])
        self.assertEqual("+ \t \t \t^\n", diff[1])
        self.assertEqual("? \t \t \t +\n", diff[2])