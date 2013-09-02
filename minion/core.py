from minion.request import WSGIRequest
from minion.routers import SimpleRouter


class Application(object):
    def __init__(self, router=None):
        if router is None:
            router = SimpleRouter()
        self.router = router

    def route(self, route):
        def _add_route(fn):
            self.router.add_route(route, fn)
            return fn
        return _add_route

    def serve(self, request):
        view, kwargs = self.router.match(request)
        return view(request, **kwargs)


def wsgi_app(application, request_class=WSGIRequest):
    def wsgi(environ, start_response):
        request = request_class(environ)
        response = application.serve(request)
        start_response(response.status, response.headers)
        return [response.content]
    return wsgi
