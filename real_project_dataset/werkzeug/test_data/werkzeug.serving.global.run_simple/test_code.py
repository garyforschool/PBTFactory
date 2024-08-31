def test_port_is_int():
    with pytest.raises(TypeError, match="port must be an integer"):
        run_simple("127.0.0.1", "5000", None)