from unittest import TestCase

from webtest import TestApp

from minion import Application, Request, Response, wsgi_app
from minion.routers import SimpleRouter


class TestMinion(TestCase):
    def test_it_routes_simple_views(self):
        minion = Application(router=SimpleRouter())

        @minion.route("/show")
        def show(request):
            return Response(b"Hello World!")

        response = minion.serve(Request(path="/show"))
        self.assertEqual(response, Response(b"Hello World!"))


class TestWSGIMinion(TestCase):
    def test_it_speaks_wsgi(self):
        minion = Application()

        @minion.route("/respond")
        def show(request):
            return Response(b"Yep!")

        wsgi = TestApp(wsgi_app(minion))
        response = wsgi.get("/respond", status=200)
        self.assertEqual(response.body, b"Yep!")

    def test_it_sets_headers(self):
        minion = Application()

        @minion.route("/respond")
        def show(request):
            return Response(
                b"{}",
                headers={"Content-Type" : "application/json"}
            )

        wsgi = TestApp(wsgi_app(minion))
        response = wsgi.get("/respond", status=200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
