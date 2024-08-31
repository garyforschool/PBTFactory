def test_integration_path(self):
        val = "~/*"
        try:
            list(find_paths(val))
        except Exception as e:
            self.fail("There was an exception: %s" % e)