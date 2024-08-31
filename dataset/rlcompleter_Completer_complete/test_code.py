    def test_complete(self):
        completer = rlcompleter.Completer()
        self.assertEqual(completer.complete('', 0), '\t')
        self.assertEqual(completer.complete('a', 0), 'and ')
        self.assertEqual(completer.complete('a', 1), 'as ')
        self.assertEqual(completer.complete('as', 2), 'assert ')
        self.assertEqual(completer.complete('an', 0), 'and ')
        self.assertEqual(completer.complete('pa', 0), 'pass')
        self.assertEqual(completer.complete('Fa', 0), 'False')
        self.assertEqual(completer.complete('el', 0), 'elif ')
        self.assertEqual(completer.complete('el', 1), 'else')
        self.assertEqual(completer.complete('tr', 0), 'try:')

    def test_duplicate_globals(self):
        namespace = {
            'False': None,  # Keyword vs builtin vs namespace
            'assert': None,  # Keyword vs namespace
            'try': lambda: None,  # Keyword vs callable
            'memoryview': None,  # Callable builtin vs non-callable
            'Ellipsis': lambda: None,  # Non-callable builtin vs callable
        }
        completer = rlcompleter.Completer(namespace)
        self.assertEqual(completer.complete('False', 0), 'False')
        self.assertIsNone(completer.complete('False', 1))  # No duplicates
        # Space or colon added due to being a reserved keyword
        self.assertEqual(completer.complete('assert', 0), 'assert ')
        self.assertIsNone(completer.complete('assert', 1))
        self.assertEqual(completer.complete('try', 0), 'try:')
        self.assertIsNone(completer.complete('try', 1))
        # No opening bracket "(" because we overrode the built-in class
        self.assertEqual(completer.complete('memoryview', 0), 'memoryview')
        self.assertIsNone(completer.complete('memoryview', 1))
        self.assertEqual(completer.complete('Ellipsis', 0), 'Ellipsis()')
        self.assertIsNone(completer.complete('Ellipsis', 1))
