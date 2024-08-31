def test_get_os_user_name_is_none(self):
        user_obj = get_os_user()
        self.getpwuid.assert_not_called()
        self.assertEqual(user_obj.pw_name, "test_user")
        self.getpwnam.assert_called_with("test_user")

def test_get_os_user_name_is_given(self):
        user_obj = get_os_user("test_user")
        self.getpwuid.assert_not_called()
        self.assertEqual(user_obj.pw_name, "test_user")
        self.getuser.assert_not_called()
        self.getpwnam.assert_called_with("test_user")

def test_get_os_user_uid(self):
        user_obj = get_os_user(254)
        self.assertEqual(user_obj.pw_name, "uid_user")
        self.getpwuid.assert_called_with(254)
        self.getuser.assert_not_called()
        self.getpwnam.assert_not_called()