"""
Fundamental routing building blocks: routers and dispatchers.

This module defines implementations of the two central routing objects:
routers and dispatchers.

A router maps URLs to "view" names. A dispatcher calls a view and passes along
any additional arguments (besides the request object).

"""

try:
    import routes
except ImportError:
    routes = None


if routes is not None:
    class RoutesRouter(object):
        def __init__(self, mapper=None):
            if mapper is None:
                mapper = routes.Mapper()
            self._mapper = mapper

        def add_route(self, route, fn, **kwargs):
            self._mapper.connect(None, route, minion_target=fn, **kwargs)

        def match(self, request):
            match = self._mapper.match(request.path)
            fn = match.pop("minion_target")
            return fn, match


class SimpleRouter(object):
    def __init__(self, routes=None):
        if routes is None:
            routes = {}
        self.routes = routes

    def add_route(self, route, fn):
        self.routes[route] = fn

    def match(self, request):
        return self.routes.get(request.path), {}
