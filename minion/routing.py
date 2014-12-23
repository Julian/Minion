"""
Routing building blocks.

There are two fundamental objects responsible for routing:

    * Mappers map a URL (an instance of :class:`bytes`) to a view (a
        callable) with some optional additional arguments
    * Routers coordinate the entire routing process, taking a request
        and returning a response, typically by composing with and invoking
        one or more Mappers.

This module defines (different) implementations which can be combined to
perform these operations in various ways.

"""

from collections import defaultdict
from functools import wraps

from characteristic import Attribute, attributes

from minion.compat import items, urlencode
from minion.request import Response, redirect
from minion.traversal import traverse


@attributes([Attribute(name="mapper")])
class Router(object):
    def add(
        self,
        route,
        fn,
        renderer=None,
        route_name=None,
        methods=(b"GET", b"HEAD"),
        **kw
    ):
        if renderer is None:
            view = fn
        else:
            @wraps(fn)
            def view(request, **kwargs):
                return renderer.render(fn(request, **kwargs))

        self.mapper.add(
            route, view, route_name=route_name, methods=methods, **kw
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
        A mapper that maps via `routes <http://routes.readthedocs.org/>`_.

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
        A mapper that uses Werkzeug's routing.

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
    Object-traversal based mapper for traversal of resource objects.

    """

    def __init__(self, root, static_mapper=None):
        if static_mapper is None:
            static_mapper = SimpleMapper()
        self.root = root

        self.static_mapper = static_mapper
        self.add = static_mapper.add
        self.lookup = static_mapper.lookup

    def map(self, request):
        static_map, static_kwargs = self.static_mapper.map(request=request)
        if static_map is not None:
            return static_map, static_kwargs
        resource = traverse(request=request, resource=self.root)
        return resource.render, {}


class SimpleMapper(object):
    """
    Simple dictionary based lookup-routing without parameters.

    """

    def __init__(self):
        self._routes = defaultdict(dict)
        self._names = {}

    def add(self, route, fn, route_name=None, methods=(b"GET", b"HEAD")):
        for method in methods:
            self._routes[method][route] = fn
        if route_name is not None:
            self._names[route_name] = route

    def map(self, request):
        fn = self._routes[request.method].get(request.path)
        return fn, {}

    def lookup(self, route_name, **kwargs):
        url = self._names.get(route_name, route_name)
        if kwargs:
            url += b"?" + urlencode(items(kwargs))
        return url
