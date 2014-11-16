from unittest import TestCase

from minion import Application, Response
from minion.request import Request
from minion.routers import SimpleRouter


class TestMinion(TestCase):
    def test_it_routes_simple_views(self):
        minion = Application(router=SimpleRouter())

        @minion.route(b"/show")
        def show(request):
            return Response(b"Hello World!")

        response = minion.serve(Request(path=b"/show"))
        self.assertEqual(response, Response(b"Hello World!"))
