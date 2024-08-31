    def longer_match_exists(self, a, b, n):
        return any(b_part in a for b_part in
                   [b[i:i + n + 1] for i in range(0, len(b) - n - 1)])

    def test_default_args(self):
        a = 'foo bar'
        b = 'foo baz bar'
        sm = difflib.SequenceMatcher(a=a, b=b)
        match = sm.find_longest_match()
        self.assertEqual(match.a, 0)
        self.assertEqual(match.b, 0)
        self.assertEqual(match.size, 6)
        self.assertEqual(a[match.a: match.a + match.size],
                         b[match.b: match.b + match.size])
        self.assertFalse(self.longer_match_exists(a, b, match.size))

        match = sm.find_longest_match(alo=2, blo=4)
        self.assertEqual(match.a, 3)
        self.assertEqual(match.b, 7)
        self.assertEqual(match.size, 4)
        self.assertEqual(a[match.a: match.a + match.size],
                         b[match.b: match.b + match.size])
        self.assertFalse(self.longer_match_exists(a[2:], b[4:], match.size))

        match = sm.find_longest_match(bhi=5, blo=1)
        self.assertEqual(match.a, 1)
        self.assertEqual(match.b, 1)
        self.assertEqual(match.size, 4)
        self.assertEqual(a[match.a: match.a + match.size],
                         b[match.b: match.b + match.size])
        self.assertFalse(self.longer_match_exists(a, b[1:5], match.size))

    def test_longest_match_with_popular_chars(self):
        a = 'dabcd'
        b = 'd'*100 + 'abc' + 'd'*100  # length over 200 so popular used
        sm = difflib.SequenceMatcher(a=a, b=b)
        match = sm.find_longest_match(0, len(a), 0, len(b))
        self.assertEqual(match.a, 0)
        self.assertEqual(match.b, 99)
        self.assertEqual(match.size, 5)
        self.assertEqual(a[match.a: match.a + match.size],
                         b[match.b: match.b + match.size])
        self.assertFalse(self.longer_match_exists(a, b, match.size))
