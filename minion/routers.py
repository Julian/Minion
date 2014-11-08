"""
Fundamental routing building blocks.

This module defines (different) implementations of routers -- objects which map
(URL) paths to views and view arguments.

"""

from minion.compat import urlencode
from minion.request import redirect
from minion.traversal import traverse


try:
    import routes
except ImportError:
    pass
else:
    class RoutesRouter(object):
        """
        A router that routes with `routes <http://routes.readthedocs.org/>`_.

        """

        def __init__(self, mapper=None):
            if mapper is None:
                mapper = routes.Mapper()
            self._generator = routes.URLGenerator(mapper, {})  # XXX: environ
            self._mapper = mapper

        def add_route(self, route, fn, route_name=None, methods=None, **kwargs):
            if methods is not None:
                kwargs.setdefault("conditions", {})["method"] = methods
            self._mapper.connect(route_name, route, minion_target=fn, **kwargs)

        def match(self, request):
            match = self._mapper.match(
                request.path,
                # Yes seriously. This seems to be the only way to do this.
                environ={"REQUEST_METHOD" : request.method},
            )
            if match is None:
                return None, {}

            fn = match.pop("minion_target")
            return fn, match

        def url_for(self, route_name, **kwargs):
            return self._generator(route_name, **kwargs)


try:
    import werkzeug.routing
except ImportError:
    pass
else:
    class WerkzeugRouter(object):
        """
        A router that uses Werkzeug's routing.

        """

        def __init__(self, map=None):
            if map is None:
                map = werkzeug.routing.Map()
            self._endpoints = {}
            self._map = map
            self._adapter = self._map.bind("")  # XXX: server_name

        def add_route(self, route, fn, route_name=None, methods=None, **kwargs):
            if methods is not None:
                kwargs["methods"] = methods
            endpoint = route_name or fn
            self._endpoints[endpoint] = fn
            rule = werkzeug.routing.Rule(route, endpoint=endpoint, **kwargs)
            self._map.add(rule)

        def match(self, request):
            try:
                return self._adapter.match(
                    path_info=request.path, method=request.method,
                )
            except werkzeug.routing.RequestRedirect as redirect_exception:
                return lambda request : redirect(
                    to=redirect_exception.new_url,
                    code=redirect_exception.code,
                ), {}
            except werkzeug.routing.HTTPException:
                return None, {}

        def url_for(self, route_name, **kwargs):
            try:
                return self._adapter.build(route_name, kwargs)
            except werkzeug.routing.BuildError as error:
                return route_name


class TraversalRouter(object):
    """
    Object-traversal based router for traversal of resource objects.

    """

    def __init__(self, root, static_router=None):
        if static_router is None:
            static_router = SimpleRouter()
        self.root = root
        self.static_router = static_router

    def add_route(self, route, fn, **kwargs):
        self.static_router.add_route(route=route, fn=fn, **kwargs)

    def match(self, request):
        static_match, static_kwargs = self.static_router.match(request=request)
        if static_match is not None:
            return static_match, static_kwargs
        resource = traverse(request=request, resource=self.root)
        return resource.render, {}

    def url_for(self, route_name, **kwargs):
        return self.static_router.url_for(route_name=route_name, **kwargs)


class SimpleRouter(object):
    """
    Simple dictionary based lookup-routing without parameters.

    """

    def __init__(self, routes=None, names=None):
        if routes is None:
            routes = {}
        if names is None:
            names = {}
        self.routes = routes
        self._names = names

    def add_route(self, route, fn, route_name=None, methods=("GET", "HEAD")):
        self.routes[route] = fn, methods
        if route_name is not None:
            self._names[route_name] = route

    def match(self, request):
        fn, methods = self.routes.get(request.path, (None, None))
        if methods is not None and request.method not in methods:
            return None, {}
        return fn, {}

    def url_for(self, route_name, **kwargs):
        url = self._names.get(route_name, route_name)
        if kwargs:
            url += "?" + urlencode(kwargs)
        return url
