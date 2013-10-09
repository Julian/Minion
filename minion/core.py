from collections import defaultdict

from minion import resource
from minion.compat import items
from minion.request import Response, WSGIRequest
from minion.routers import SimpleRouter


class Application(object):
    def __init__(self, config=None, bin=None, router=None, jinja=None):
        if config is None:
            config = {}
        if bin is None:
            bin = resource.Bin()
        if router is None:
            router = SimpleRouter()

        self._response_callbacks = defaultdict(list)

        self.bin = bin
        self.config = config
        self.router = router

        self.bind_bin(bin)
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
            response = view(request, **kwargs)
        else:
            response = Response(code=404)

        callbacks = self._response_callbacks.pop(request, None)
        if callbacks is not None:
            for fn, args, kwargs in callbacks:
                callback_response = fn(request, response, *args, **kwargs)
                if callback_response is not None:
                    response = callback_response

        return response

    def after_response(self, request, fn, *fnargs, **fnkwargs):
        """
        Call the given callable after the given request has its response.

        """

        self._response_callbacks[request].append((fn, fnargs, fnkwargs))

    def bind_bin(self, bin):
        """
        Bind a resource bin to this application.

        Simply adds the application to the bin globals.

        """

        bin.globals.update([
            ("app", self),
            ("config", self.config),
            ("router", self.router),
        ])

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
            ("config", self.config),
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
