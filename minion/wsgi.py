class WSGIRequest(object):
    def __init__(self, environ):
        self.environ = environ

    @property
    def method(self):
        return self.environ["REQUEST_METHOD"]

    @property
    def path(self):
        return self.environ["PATH_INFO"]


def wsgi_app(application, request_class=WSGIRequest):
    """
    Create a WSGI application out of the given Minion app.

    :argument Application application: a minion app
    :argument request_class: a class to use for constructing incoming requests
        out of the WSGI environment. It will be passed a single arg, the
        environ. By default, this is :class:`minion.request.WSGIRequest` if
        unprovided.

    """

    def wsgi(environ, start_response):
        request = request_class(environ)
        response = application.serve(request)
        start_response(
            response.status, [
                (name, b",".join(values))
                for name, values in response.headers.canonicalized()
            ],
        )
        return [response.content]
    return wsgi
