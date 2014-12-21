"""
Fundamental routing building blocks.

This module defines (different) implementations of routers -- objects which map
(URL) paths to views and view arguments.

"""

from characteristic import Attribute, attributes

from minion.compat import items, urlencode
from minion.request import Response, redirect
from minion.traversal import traverse


@attributes([Attribute(name="mapper")])
class Router(object):
    def add(self, route, fn, route_name=None, methods=(b"GET", b"HEAD"), **kw):
        self.mapper.add(
            route, fn, route_name=route_name, methods=methods, **kw
        )

    def route(self, request):
        view, kwargs = self.mapper.map(request)
        if view is not None:
            response = view(request=request, **kwargs)
        else:
            response = Response(code=404)
        return response


try:
    import routes
except ImportError:
    pass
else:
    class RoutesMapper(object):
        """
        A router that routes with `routes <http://routes.readthedocs.org/>`_.

        """

        def __init__(self, mapper=None):
            if mapper is None:
                mapper = routes.Mapper()
            self._generator = routes.URLGenerator(mapper, {})  # XXX: environ
            self._mapper = mapper

        def add(self, route, fn, route_name=None, methods=None, **kwargs):
            if methods is not None:
                kwargs.setdefault("conditions", {})["method"] = methods
            self._mapper.connect(route_name, route, minion_target=fn, **kwargs)

        def map(self, request):
            match = self._mapper.match(
                request.path,
                # Yes seriously. This seems to be the only way to do this.
                environ={"REQUEST_METHOD" : request.method},
            )
            if match is None:
                return None, {}

            fn = match.pop("minion_target")
            return fn, match

        def lookup(self, route_name, **kwargs):
            return self._generator(route_name, **kwargs)


try:
    import werkzeug.routing
except ImportError:
    pass
else:
    class WerkzeugMapper(object):
        """
        A router that uses Werkzeug's routing.

        """

        def __init__(self, map=None):
            if map is None:
                map = werkzeug.routing.Map()
            self._endpoints = {}
            self._map = map
            self._adapter = self._map.bind(b"")  # XXX: server_name

        def add(self, route, fn, route_name=None, methods=None, **kwargs):
            if methods is not None:
                kwargs["methods"] = methods
            endpoint = route_name or fn
            self._endpoints[endpoint] = fn
            rule = werkzeug.routing.Rule(route, endpoint=endpoint, **kwargs)
            self._map.add(rule)

        def map(self, request):
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

        def lookup(self, route_name, **kwargs):
            try:
                return self._adapter.build(route_name, kwargs)
            except werkzeug.routing.BuildError:
                return route_name


class TraversalMapper(object):
    """
    Object-traversal based router for traversal of resource objects.

    """

    def __init__(self, root, static_router=None):
        if static_router is None:
            static_router = SimpleMapper()
        self.root = root

        self.static_router = static_router
        self.add = static_router.add
        self.lookup = static_router.lookup

    def map(self, request):
        static_map, static_kwargs = self.static_router.map(request=request)
        if static_map is not None:
            return static_map, static_kwargs
        resource = traverse(request=request, resource=self.root)
        return resource.render, {}


class SimpleMapper(object):
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

    def add(self, route, fn, route_name=None, methods=(b"GET", b"HEAD")):
        self.routes[route] = fn, methods
        if route_name is not None:
            self._names[route_name] = route

    def map(self, request):
        fn, methods = self.routes.get(request.path, (None, None))
        if methods is not None and request.method not in methods:
            return None, {}
        return fn, {}

    def lookup(self, route_name, **kwargs):
        url = self._names.get(route_name, route_name)
        if kwargs:
            url += b"?" + urlencode(items(kwargs))
        return url
