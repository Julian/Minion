from unittest import TestCase
import mock

from minion import routers
from minion.request import Request


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
