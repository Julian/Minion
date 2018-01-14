from unittest import TestCase, skipIf

from future.utils import PY3
from hyperlink import URL
from webtest import TestApp
from werkzeug.test import create_environ

from minion import wsgi
from minion.core import Application
from minion.http import Headers
from minion.request import Response
from minion.tests.test_integration import RequestIntegrationTestMixin
from minion.tests.test_request import RequestTestMixin


@skipIf(PY3, "WSGI is pure insanity on Py3")
class TestWSGIMinion(TestCase):
    def setUp(self):
        self.minion = Application()
        self.wsgi = TestApp(wsgi.create_app(self.minion))

    def test_it_speaks_wsgi(self):
        @self.minion.route(b"/respond")
        def respond(request):
            return Response(b"Yep!")

        response = self.wsgi.get("/respond", status=200)
        self.assertEqual(response.body, b"Yep!")

    def test_it_parses_headers(self):
        @self.minion.route(b"/respond")
        def respond(request):
            return Response(request.headers.get("Accept")[0])

        response = self.wsgi.get(
            b"/respond", status=200, headers={b"Accept": b"2"},
        )
        self.assertEqual(response.body, b"2")

    def test_it_parses_response_bodies(self):
        @self.minion.route(b"/respond", methods=["POST"])
        def respond(request):
            return Response(request.content.read())

        response = self.wsgi.post(
            b"/respond",
            params=b"Check out this body.",
            status=200,
        )
        self.assertEqual(response.body, b"Check out this body.")

    def test_it_sets_headers(self):
        @self.minion.route(b"/respond")
        def respond(request):
            return Response(
                b"{}",
                headers=Headers([(b"Content-Type", [b"application/json"])]),
            )

        response = self.wsgi.get(b"/respond", status=200)
        self.assertEqual(
            response.headers[b"Content-Type"],
            b"application/json",
        )


class TestRequest(RequestTestMixin, TestCase):
    def make_request(self, headers):
        headers = {k: b",".join(v) for k, v in headers.canonicalized()}
        return wsgi.Request(environ=create_environ(headers=headers))

    def test_query_string(self):
        environ = {
            "SERVER_NAME": "example.com",
            "SERVER_PORT": "80",
            "QUERY_STRING": "foo=bar",
            "wsgi.url_scheme": "http",
        }
        self.assertEqual(
            wsgi.Request(environ).url, URL(
                scheme=u"http",
                host=u"example.com",
                query=[(u"foo", u"bar")],
            ),
        )

    def test_default_port(self):
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "80",
            "wsgi.url_scheme": "http",
        }
        self.assertEqual(
            wsgi.Request(environ).url,
            URL(scheme=u"http", host=u"localhost", port=None),
        )

    def test_non_default_port(self):
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "wsgi.url_scheme": "http",
        }
        self.assertEqual(
            wsgi.Request(environ).url,
            URL(scheme=u"http", host=u"localhost", port=8080),
        )

    def test_http_host_present(self):
        environ = {
            "HTTP_HOST": "example.org:1234",
            "PATH_INFO": "/",
            "SERVER_PORT": "1234",
            "wsgi.url_scheme": "https",
        }
        self.assertEqual(
            wsgi.Request(environ).url, URL(
                scheme=u"https",
                host=u"example.org",
                path=[u""],
                port=1234,
            ),
        )

    def test_http_host_present_default_port(self):
        environ = {
            "HTTP_HOST": "example.org:80",
            "SERVER_PORT": "80",
            "PATH_INFO": "/",
            "wsgi.url_scheme": "https",
        }
        self.assertEqual(
            wsgi.Request(environ).url, URL(
                scheme=u"https",
                host=u"example.org",
                path=[u""],
                port=80,
            ),
        )

    def test_no_http_host_present(self):
        environ = {
            "SERVER_NAME": "example.org",
            "SERVER_PORT": "1234",
            "PATH_INFO": "/",
            "wsgi.url_scheme": "https",
        }
        self.assertEqual(
            wsgi.Request(environ).url, URL(
                scheme=u"https",
                host=u"example.org",
                path=[u""],
                port=1234,
            ),
        )

    def test_script_name(self):
        environ = {
            "HTTP_HOST": "example.org",
            "SCRIPT_NAME": "/stuff",
            "PATH_INFO": "/things",
            "SERVER_PORT": "443",
            "wsgi.url_scheme": "https",
        }
        self.assertEqual(
            wsgi.Request(environ).url, URL(
                scheme=u"https",
                host=u"example.org",
                path=[u"stuff", u"things"],
            ),
        )

    def test_host_no_path_no_query_string(self):
        environ = {
            "HTTP_HOST": "example.com",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "80",
            "wsgi.url_scheme": "http",
        }
        self.assertEqual(
            wsgi.Request(environ).url,
            URL(scheme=u"http", host=u"example.com"),
        )

    def test_no_host_no_path_no_query_string(self):
        environ = {
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "80",
            "wsgi.url_scheme": "http",
        }
        self.assertEqual(
            wsgi.Request(environ).url,
            URL(scheme=u"http", host=u"localhost"),
        )


class TestRequestIntegration(RequestIntegrationTestMixin, TestCase):
    def get(self, url, headers):
        app = TestApp(wsgi.create_app(self.minion))
        response = app.get(
            url,
            headers=[(k, b",".join(v)) for k, v in headers.canonicalized()],
        )
        return response.body

    def test_script_name(self):
        self.minion.route(b"/home")(lambda request: Response(b"Hi!"))
        app = TestApp(
            wsgi.create_app(self.minion),
            extra_environ={"SCRIPT_NAME": "/app"},
        )
        response = app.get(b"/app/home")
        self.assertEqual(response.body, b"Hi!")
