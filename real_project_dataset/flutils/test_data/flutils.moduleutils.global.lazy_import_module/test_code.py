def test_integration_lazy_import(self):
        mod = lazy_import_module(".lazy", package=self.package)
        mod.test = 6
        mod.a_val = 22
        mod.foo = 33
        self.assertEqual(False, mod.is_loaded)
        val = mod.get_lazy_value()
        self.assertEqual(val, 3)
        self.assertEqual(33, mod.foo)
        self.assertEqual(6, mod.test)
        self.assertEqual(22, mod.a_val)

def test_integration_lazy1_import(self):
        mod = lazy_import_module(".lazy1", package=self.package)
        mod.test = 6
        mod.a_val = 22
        mod.foo = 33
        mod.bar = 1
        del mod.bar
        self.assertEqual(True, mod.is_loaded)
        val = mod.one()
        self.assertEqual(val, 88)
        self.assertEqual(33, mod.foo)
        self.assertEqual(6, mod.test)
        self.assertEqual(22, mod.a_val)

def test_lazy_import_module(self):
        mod = lazy_import_module("foo")
        self.find_spec.assert_called_once_with("foo")
        self.lazy_loader.assert_called_once()

def test_lazy_import_module_with_package(self):
        lazy_import_module("foo", package="bar")
        self.find_spec.assert_called_once_with("foo")
        self.lazy_loader.assert_called_once()

def test_lazy_import_module_already_loaded(self):
        _ = lazy_import_module("foo")
        self.find_spec.assert_not_called()
        self.lazy_loader.assert_not_called()

def test_lazy_import_module_no_spec(self):
        with self.assertRaises(ImportError):
            lazy_import_module("foo")
        self.find_spec.assert_called_once()