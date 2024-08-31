def test_parse_attr_map(self):
        res = _parse_attr_map(self.attr_map, "foo")
        self._expand_attr_map.assert_called_once_with(self.attr_map)
        expect = {"os.path": self.return_value}
        self.assertEqual(res.modules, expect)
        expect = dict(dname="os.path", basename="os.path")
        self.assertEqual(res.identifiers, expect)

def test_parse_attr_map_duplicate(self):
        with self.assertRaises(CherryPickError):
            _parse_attr_map(self.attr_map, "foo")
        self._expand_attr_map.assert_called_once_with(self.attr_map)