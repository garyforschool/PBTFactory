def test_path_info_and_script_name_fetching():
    env = create_environ("/☃", "http://example.com/☄/")
    assert wsgi.get_path_info(env) == "/☃"