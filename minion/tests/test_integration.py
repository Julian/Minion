from unittest import TestCase
import json

from hyperlink import URL

from minion.core import Application
from minion.http import Headers
from minion.renderers import JSON
from minion.request import Request, Response
from minion.routing import Router, SimpleMapper


class TestMinion(TestCase):
    def test_it_routes_simple_views(self):
        minion = Application(router=Router(mapper=SimpleMapper()))

        @minion.route(b"/show")
        def show(request):
            return Response(b"Hello World!")

        url = URL(path=[u"show"])
        response = minion.serve(Request(url=url), path=u"/show")
        self.assertEqual(response, Response(b"Hello World!"))


class RequestIntegrationTestMixin(object):
    def setUp(self):
        self.minion = Application()

        @self.minion.route(b"/respond", renderer=JSON())
        def respond(request):
            return {"url": request.url.to_text().encode("utf-8")}

    def get_request(self, *args, **kwargs):
        kwargs.setdefault("headers", Headers())
        response = json.loads(self.get(*args, **kwargs))
        response["url"] = URL.from_text(response["url"].decode("utf-8"))
        return Request(**response)

    def test_it_parses_the_url(self):
        request = self.get_request(
            b"/respond?foo=bar#baz",
            headers=Headers([(b"Host", [b"example.com"])]),
        )
        self.assertEqual(
            request.url, URL(
                scheme=u"http",
                host=u"example.com",
                path=[u"respond"],
                query=[(u"foo", u"bar")],
                fragment=u"",  # Fragments should be ignored by servers.
            ),
        )
