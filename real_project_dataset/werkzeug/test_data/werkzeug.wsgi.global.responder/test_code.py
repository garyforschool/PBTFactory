def test_responder():

    def foo(environ, start_response):
        return Response(b"Test")

    client = Client(wsgi.responder(foo))
    response = client.get("/")
    assert response.status_code == 200
    assert response.data == b"Test"