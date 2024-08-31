def test_delete_requests_with_form():

    @Request.application
    def test_app(request):
        return Response(request.form.get("x", None))

    client = Client(test_app)
    resp = client.delete("/", data={"x": 42})
    assert resp.text == "42"