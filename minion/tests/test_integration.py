from unittest import TestCase

from minion.core import Application
from minion.http import URL
from minion.request import Request, Response
from minion.routing import Router, SimpleMapper


class TestMinion(TestCase):
    def test_it_routes_simple_views(self):
        minion = Application(router=Router(mapper=SimpleMapper()))

        @minion.route(b"/show")
        def show(request):
            return Response(b"Hello World!")

        response = minion.serve(Request(url=URL(path=b"/show")))
        self.assertEqual(response, Response(b"Hello World!"))
