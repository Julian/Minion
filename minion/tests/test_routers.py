from unittest import TestCase, skipIf
import mock

from minion import routers
from minion.request import Request


class RouterTestMixin(object):
    """
    Test basic functionality common to all routers.

    Expects a router to be present and instantiated at the `router` attribute
    of the test case.

    """

    def test_it_routes_routes(self):
        fn = mock.Mock()
        self.router.add_route("/route", fn)
        matched = self.router.match(Request(path="/route"))
        self.assertEqual(matched, (fn, {}))

    def test_it_routes_routes_for_specified_methods(self):
        fn = mock.Mock()
        self.router.add_route("/route", fn, methods=["POST"])
        matched = self.router.match(Request(path="/route", method="POST"))
        self.assertEqual(matched, (fn, {}))

    def test_it_does_not_route_routes_for_unspecified_methods(self):
        fn = mock.Mock()
        self.router.add_route("/route", fn, methods=["POST"])
        matched = self.router.match(Request(path="/route", method="GET"))
        self.assertEqual(matched, (None, {}))

    def test_it_does_not_route_unknown_paths(self):
        matched = self.router.match(Request(path="/route"))
        self.assertEqual(matched, (None, {}))


@skipIf(not hasattr(routers, "RoutesRouter"), "routes not found")
class TestRoutesRouter(RouterTestMixin, TestCase):
    def setUp(self):
        self.router = routers.RoutesRouter()

    def test_it_routes_routes_with_arguments(self):
        fn = mock.Mock()
        self.router.add_route("/route/{year}", fn, stuff="12")
        matched = self.router.match(Request(path="/route/2013"))
        self.assertEqual(matched, (fn, {"year" : "2013", "stuff" : "12"}))


@skipIf(not hasattr(routers, "WerkzeugRouter"), "werkzeug not found")
class TestWerkzeugRouter(RouterTestMixin, TestCase):
    def setUp(self):
        self.router = routers.WerkzeugRouter()

    def test_it_routes_routes_with_arguments(self):
        fn = mock.Mock()
        self.router.add_route("/route/<int:year>", fn)
        matched = self.router.match(Request(path="/route/2013"))
        self.assertEqual(matched, (fn, {"year" : 2013}))


class TestSimpleRouter(RouterTestMixin, TestCase):
    def setUp(self):
        self.router = routers.SimpleRouter()
