def test_secure_filename():
    assert utils.secure_filename("My cool movie.mov") == "My_cool_movie.mov"
    assert utils.secure_filename("../../../etc/passwd") == "etc_passwd"
    assert (
        utils.secure_filename("i contain cool ümläuts.txt")
        == "i_contain_cool_umlauts.txt"
    )
    assert utils.secure_filename("__filename__") == "filename"
    assert utils.secure_filename("foo$&^*)bar") == "foobar"