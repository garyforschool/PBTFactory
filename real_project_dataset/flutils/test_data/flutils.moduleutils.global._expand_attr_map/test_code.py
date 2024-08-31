def test_expand_attr_map(self):
        val = list(_expand_attr_map((self.item,)))
        self.assertEqual(val, [self.return_value])

def test_expand_attr_map_no_duplicates(self):
        attr_map = self.item, self.item
        val = list(_expand_attr_map(attr_map))
        self.assertEqual(val, [self.return_value])