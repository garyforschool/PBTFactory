def test_get_os_group_name_is_none(self):
        group_obj = get_os_group()
        self.assertEqual(group_obj.gr_name, "foo")
        self.getgrnam.assert_not_called()

def test_get_os_group_name_is_given(self):
        group_obj = get_os_group("test_group")
        self.assertEqual(group_obj.gr_name, "foo")
        self.getgrnam.assert_called_with("test_group")
        self.get_os_user.assert_not_called()
        self.getgrgid.assert_not_called()

def test_get_os_group_name_is_gid(self):
        group_obj = get_os_group(254)
        self.get_os_user.assert_not_called()
        self.getgrgid.assert_called_once_with(254)
        self.assertEqual(group_obj.gr_name, "foo")
        self.getgrnam.assert_not_called()