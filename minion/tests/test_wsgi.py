from unittest import TestCase, skipIf

from webtest import TestApp

from minion import Application, Response
from minion.compat import PY3
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

    def test_it_parses_headers(self):
        minion = Application()

        @minion.route("/respond")
        def show(request):
            return Response(request.headers.get("Accept")[0])

        wsgi = TestApp(wsgi_app(minion))
        response = wsgi.get("/respond", status=200, headers={b"Accept" : b"2"})
        self.assertEqual(response.body, b"2")

    @skipIf(PY3, "WSGI is pure insanity on Py3")
    def test_it_sets_headers(self):
        minion = Application()

        @minion.route(b"/respond")
        def show(request):
            return Response(
                b"{}",
                headers=Headers([(b"Content-Type", [b"application/json"])]),
            )

        wsgi = TestApp(wsgi_app(minion))
        response = wsgi.get(b"/respond", status=200)
        self.assertEqual(
            response.headers[b"Content-Type"],
            b"application/json",
        )
