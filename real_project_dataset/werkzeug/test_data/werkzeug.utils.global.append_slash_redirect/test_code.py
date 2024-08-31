@Request.application
    def app(request):
        rv = utils.append_slash_redirect(request.environ)
        rv.autocorrect_location_header = autocorrect
        return rv