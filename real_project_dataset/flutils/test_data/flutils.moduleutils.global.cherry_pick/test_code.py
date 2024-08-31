def test_cherry_pick(self):
        cherry_pick(self.namespace)
        kwargs = dict()
        kwargs["__loader__"] = sentinel.loader
        kwargs["__path__"] = self.namespace["__path__"]
        kwargs["__file__"] = self.namespace["__file__"]
        kwargs.update(self.additional_attrs)
        self.add.assert_called_once_with(
            "testmod",
            self.namespace["__file__"],
            self.namespace["__path__"],
            self.attr_map,
            **kwargs
        )
        self.reload.assert_called_once_with(sentinel.testmod)
        self.import_module.assert_not_called()

def test_cherry_pick_empty_additional_attrs(self):
        namespace = self.namespace.copy()
        del namespace["__additional_attrs__"]
        cherry_pick(namespace)
        kwargs = dict()
        kwargs["__loader__"] = sentinel.loader
        kwargs["__path__"] = self.namespace["__path__"]
        kwargs["__file__"] = self.namespace["__file__"]
        self.add.assert_called_once_with(
            "testmod",
            self.namespace["__file__"],
            self.namespace["__path__"],
            self.attr_map,
            **kwargs
        )
        self.reload.assert_called_once_with(sentinel.testmod)
        self.import_module.assert_not_called()

def test_cherry_pick_import_module(self):
        cherry_pick(self.namespace)
        kwargs = dict()
        kwargs["__loader__"] = sentinel.loader
        kwargs["__path__"] = self.namespace["__path__"]
        kwargs["__file__"] = self.namespace["__file__"]
        kwargs.update(self.additional_attrs)
        self.add.assert_called_once_with(
            "testmod",
            self.namespace["__file__"],
            self.namespace["__path__"],
            self.attr_map,
            **kwargs
        )
        self.reload.assert_not_called()
        self.import_module.assert_called_once_with("testmod")

def test_cherry_pick_find_spec_raises(self):
        with self.assertRaises(ImportError):
            cherry_pick(self.namespace)

def test_cherry_pick_additional_attrs_key_raises(self):
        with self.assertRaises(ImportError):
            cherry_pick(self.namespace)