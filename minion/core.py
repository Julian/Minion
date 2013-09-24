from minion.request import Response, WSGIRequest
from minion.routers import SimpleRouter


class Application(object):
    def __init__(self, router=None):
        if router is None:
            router = SimpleRouter()
        self.router = router

    def route(self, route, **kwargs):
        def _add_route(fn):
            self.router.add_route(route, fn, **kwargs)
            return fn
        return _add_route

    def serve(self, request):
        view, kwargs = self.router.match(request)
        if view is not None:
            return view(request, **kwargs)
        return Response(code=404)


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
        start_response(response.status, response.headers.items())
        return [response.content]
    return wsgi
