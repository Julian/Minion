from unittest import TestCase, skipIf
import mock

from minion import routers
from minion.request import Request


@skipIf(routers.routes is None, "routes not found")
class TestRoutesRouter(TestCase):
    def setUp(self):
        self.router = routers.RoutesRouter()

    def test_it_routes_routes(self):
        fn = mock.Mock()
        self.router.add_route("/route", fn)
        matched = self.router.match(Request(path="/route"))
        self.assertEqual(matched, (fn, {}))

    def test_it_routes_routes_with_arguments(self):
        fn = mock.Mock()
        self.router.add_route("/route/{year}", fn, stuff="12")
        matched = self.router.match(Request(path="/route/2013"))
        self.assertEqual(matched, (fn, {"year" : "2013", "stuff" : "12"}))

    def test_it_does_not_route_unknown_paths(self):
        matched = self.router.match(Request(path="/route"))
        self.assertEqual(matched, (None, {}))


class TestSimpleRouter(TestCase):
    def setUp(self):
        self.router = routers.SimpleRouter()

    def test_it_routes_literal_paths(self):
        fn = mock.Mock()
        self.router.add_route("/route", fn)
        matched = self.router.match(Request(path="/route"))
        self.assertEqual(matched, (fn, {}))

    def test_it_does_not_route_unknown_paths(self):
        matched = self.router.match(Request(path="/route"))
        self.assertEqual(matched, (None, {}))
