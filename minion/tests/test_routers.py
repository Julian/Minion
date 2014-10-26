from unittest import TestCase, skipIf

from minion import Response, routers
from minion.request import Request


def view(request):
    return Response("Is anybody out there?")


class RouterTestMixin(object):
    """
    Test basic functionality common to all routers.

    Expects a router to be present and instantiated at the `router` attribute
    of the test case.

    """

    def test_it_routes_routes(self):
        self.router.add_route("/route", view)
        matched = self.router.match(Request(path="/route"))
        self.assertEqual(matched, (view, {}))

    def test_it_routes_routes_for_specified_methods(self):
        self.router.add_route("/route", view, methods=["POST"])
        matched = self.router.match(Request(path="/route", method="POST"))
        self.assertEqual(matched, (view, {}))

    def test_it_does_not_route_routes_for_unspecified_methods(self):
        self.router.add_route("/route", view, methods=["POST"])
        matched = self.router.match(Request(path="/route", method="GET"))
        self.assertEqual(matched, (None, {}))

    def test_it_can_build_named_routes(self):
        self.router.add_route("/", view, route_name="home")
        self.assertEqual(self.router.url_for("home"), "/")

    def test_unknown_route_names_become_literal_paths(self):
        self.assertEqual(self.router.url_for("/work"), "/work")

    def test_it_does_not_route_unknown_paths(self):
        matched = self.router.match(Request(path="/route"))
        self.assertEqual(matched, (None, {}))

    def test_extra_build_arguments_become_query_strings(self):
        self.router.add_route("/", view, route_name="home")
        url = self.router.url_for("home", thing="yes")
        self.assertEqual(url, "/?thing=yes")


@skipIf(not hasattr(routers, "RoutesRouter"), "routes not found")
class TestRoutesRouter(RouterTestMixin, TestCase):
    def setUp(self):
        self.router = routers.RoutesRouter()

    def test_it_routes_routes_with_arguments(self):
        self.router.add_route("/route/{year}", view, stuff="12")
        matched = self.router.match(Request(path="/route/2013"))
        self.assertEqual(matched, (view, {"year" : "2013", "stuff" : "12"}))

    def test_it_builds_routes_with_arguments(self):
        self.router.add_route("/{year}", view, route_name="year")
        url = self.router.url_for("year", year=2012)
        self.assertEqual(url, "/2012")


@skipIf(not hasattr(routers, "WerkzeugRouter"), "werkzeug not found")
class TestWerkzeugRouter(RouterTestMixin, TestCase):
    def setUp(self):
        self.router = routers.WerkzeugRouter()

    def test_it_routes_routes_with_arguments(self):
        self.router.add_route("/route/<int:year>", view)
        matched = self.router.match(Request(path="/route/2013"))
        self.assertEqual(matched, (view, {"year" : 2013}))

    def test_it_builds_routes_with_arguments(self):
        self.router.add_route("/<int:year>", view, route_name="year")
        url = self.router.url_for("year", year=2012)
        self.assertEqual(url, "/2012")


class TestSimpleRouter(RouterTestMixin, TestCase):
    def setUp(self):
        self.router = routers.SimpleRouter()
