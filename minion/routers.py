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

        def add_route(self, route, fn, methods=None, **kwargs):
            if methods is not None:
                kwargs.setdefault("conditions", {})["method"] = methods
            self._mapper.connect(None, route, minion_target=fn, **kwargs)

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

        def add_route(self, route, fn, methods=None, **kwargs):
            if methods is not None:
                kwargs["methods"] = methods
            rule = werkzeug.routing.Rule(route, endpoint=fn, **kwargs)
            self._map.add(rule)

        def match(self, request):
            method = request.method
            if not self._adapter.test(request.path, method=method):
                return None, {}
            return self._adapter.match(path_info=request.path, method=method)



class SimpleRouter(object):
    def __init__(self, routes=None):
        if routes is None:
            routes = {}
        self.routes = routes

    def add_route(self, route, fn, methods=("GET", "HEAD")):
        self.routes[route] = fn, methods

    def match(self, request):
        fn, methods = self.routes.get(request.path, (None, None))
        if methods is not None and request.method not in methods:
            return None, {}
        return fn, {}
