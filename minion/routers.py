class SimpleRouter(object):
    def __init__(self, routes=None):
        if routes is None:
            routes = {}
        self.routes = routes

    def add_route(self, route, fn):
        self.routes[route] = fn

    def match(self, request):
        return self.routes.get(request.path), {}
