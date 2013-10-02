from minion import resource
from minion.compat import items
from minion.request import Response, WSGIRequest
from minion.routers import SimpleRouter


class Application(object):
    def __init__(self, bin=None, router=None, jinja=None):
        if bin is None:
            bin = resource.Bin()
        if router is None:
            router = SimpleRouter()

        self.bin = bin
        self.bind_bin(bin)
        self.router = router

        if jinja is not None:
            self.bind_jinja_environment(jinja)

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

    def bind_bin(self, bin):
        """
        Bind a resource bin to this application.

        Simply adds the application to the bin globals.

        """

        bin.globals["app"] = self

    def bind_jinja_environment(self, environment, resource_name="jinja"):
        """
        Bind useful pieces of the application to the given Jinja2 environment.

        :type environment: :class:`jinja2.Environment`
        :argument str resource_name: the name to bind the environment in the
            application's resource bin. The default is ``'jinja'``.

        """

        self.bin.globals[resource_name] = environment
        environment.globals.update([
            ("app", self),
            ("router", self.router),
        ])


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
        start_response(response.status, items(response.headers))
        return [response.content]
    return wsgi
