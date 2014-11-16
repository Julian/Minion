from unittest import TestCase, skipIf

from minion import Response, routers
from minion.request import Request, redirect
from minion.traversal import LeafResource


def view(request):
    return Response("Is anybody out there?")


class RouterTestMixin(object):
    """
    Test basic functionality common to all routers.

    Expects a router to be present and instantiated at the `router` attribute
    of the test case.

    """

    def test_it_routes_routes(self):
        self.router.add_route(b"/route", view)
        matched = self.router.match(Request(path=b"/route"))
        self.assertEqual(matched, (view, {}))

    def test_it_routes_routes_for_specified_methods(self):
        self.router.add_route(b"/route", view, methods=[b"POST"])
        matched = self.router.match(Request(path=b"/route", method=b"POST"))
        self.assertEqual(matched, (view, {}))

    def test_it_does_not_route_routes_for_unspecified_methods(self):
        self.router.add_route(b"/route", view, methods=[b"POST"])
        matched = self.router.match(Request(path=b"/route", method=b"GET"))
        self.assertEqual(matched, (None, {}))

    def test_it_can_build_named_routes(self):
        self.router.add_route(b"/", view, route_name=u"home")
        self.assertEqual(self.router.url_for(u"home"), b"/")

    def test_unknown_route_names_become_literal_paths(self):
        self.assertEqual(self.router.url_for(b"/work"), b"/work")

    def test_it_does_not_route_unknown_paths(self):
        matched = self.router.match(Request(path=b"/route"))
        self.assertEqual(matched, (None, {}))

    def test_extra_build_arguments_become_query_strings(self):
        self.router.add_route(b"/", view, route_name=u"home")
        url = self.router.url_for(u"home", thing=b"yes")
        self.assertEqual(url, b"/?thing=yes")


class TestTraversalRouter(TestCase):
    def test_it_traverses_children(self):
        class Resource(object):
            def get_child(self, name, request):
                return LeafResource(
                    render=lambda request : Response(b"Hello " + name),
                )

        router = routers.TraversalRouter(root=Resource())
        request = Request(path=b"/world")
        matched, kwargs = router.match(request)
        self.assertEqual(matched(request), Response(content=b"Hello world"))


class TestTraversalRouterStatic(RouterTestMixin, TestCase):
    def setUp(self):
        self.router = routers.TraversalRouter(root=LeafResource(render=None))


@skipIf(not hasattr(routers, "RoutesRouter"), "routes not found")
class TestRoutesRouter(RouterTestMixin, TestCase):
    def setUp(self):
        self.router = routers.RoutesRouter()

    def test_it_routes_routes_with_arguments(self):
        self.router.add_route(b"/route/{year}", view, stuff=b"12")
        matched = self.router.match(Request(path=b"/route/2013"))
        self.assertEqual(
            matched, (view, {b"year" : b"2013", b"stuff" : b"12"}),
        )

    def test_it_builds_routes_with_arguments(self):
        self.router.add_route(b"/{year}", view, route_name=u"year")
        url = self.router.url_for(b"year", year=2012)
        self.assertEqual(url, b"/2012")


@skipIf(not hasattr(routers, "WerkzeugRouter"), "werkzeug not found")
class TestWerkzeugRouter(RouterTestMixin, TestCase):
    def setUp(self):
        self.router = routers.WerkzeugRouter()

    def test_it_routes_routes_with_arguments(self):
        self.router.add_route(b"/route/<int:year>", view)
        matched = self.router.match(Request(path=b"/route/2013"))
        self.assertEqual(matched, (view, {b"year" : 2013}))

    def test_it_builds_routes_with_arguments(self):
        self.router.add_route(b"/<int:year>", view, route_name=u"year")
        url = self.router.url_for(u"year", year=2012)
        self.assertEqual(url, b"/2012")

    def test_it_handles_routing_redirects(self):
        self.router.add_route(b"/<int:year>/", view)
        request = Request(path=b"/2013")
        matched, _ = self.router.match(request)
        self.assertEqual(
            matched(request), redirect(b"http:///2013/", code=301),
        )


class TestSimpleRouter(RouterTestMixin, TestCase):
    def setUp(self):
        self.router = routers.SimpleRouter()
