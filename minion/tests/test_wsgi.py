from unittest import TestCase

from webtest import TestApp

from minion import Application, Response
from minion.http import Headers
from minion.wsgi import wsgi_app


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
                headers=Headers([("Content-Type", ["application/json"])]),
            )

        wsgi = TestApp(wsgi_app(minion))
        response = wsgi.get("/respond", status=200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
