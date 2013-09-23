"""
Fundamental routing building blocks.

This module defines (different) implementations of routers -- objects which map
(URL) paths to views and view arguments.

"""

try:
    import routes
except ImportError:
    pass
else:
    class RoutesRouter(object):
        def __init__(self, mapper=None):
            if mapper is None:
                mapper = routes.Mapper()
            self._mapper = mapper

        def add_route(self, route, fn, **kwargs):
            self._mapper.connect(None, route, minion_target=fn, **kwargs)

        def match(self, request):
            match = self._mapper.match(request.path)
            if match is None:
                return None, {}

            fn = match.pop("minion_target")
            return fn, match


try:
    import werkzeug.routing
except ImportError:
    pass
else:
    class WerkzeugRouter(object):
        def __init__(self, map=None):
            if map is None:
                map = werkzeug.routing.Map()
            self._map = map
            self._adapter = self._map.bind("")  # XXX: server_name

        def add_route(self, route, fn, **kwargs):
            rule = werkzeug.routing.Rule(route, endpoint=fn)
            self._map.add(rule)

        def match(self, request):
            if not self._adapter.test(request.path):
                return None, {}
            return self._adapter.match(request.path)



class SimpleRouter(object):
    def __init__(self, routes=None):
        if routes is None:
            routes = {}
        self.routes = routes

    def add_route(self, route, fn):
        self.routes[route] = fn

    def match(self, request):
        return self.routes.get(request.path), {}
