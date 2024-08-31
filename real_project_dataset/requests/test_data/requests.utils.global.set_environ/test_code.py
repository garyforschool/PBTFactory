@pytest.mark.parametrize(
    "env_name, value",
    (
        ("no_proxy", "192.168.0.0/24,127.0.0.1,localhost.localdomain"),
        ("no_proxy", None),
        ("a_new_key", "192.168.0.0/24,127.0.0.1,localhost.localdomain"),
        ("a_new_key", None),
    ),
)
def test_set_environ(env_name, value):
    environ_copy = copy.deepcopy(os.environ)
    with set_environ(env_name, value):
        assert os.environ.get(env_name) == value
    assert os.environ == environ_copy

def test_set_environ_raises_exception():
    with pytest.raises(Exception) as exception:
        with set_environ("test1", None):
            raise Exception("Expected exception")
    assert "Expected exception" in str(exception.value)