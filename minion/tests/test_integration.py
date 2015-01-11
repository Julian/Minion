from unittest import TestCase
import json

from minion.core import Application
from minion.http import Headers, URL
from minion.renderers import JSON
from minion.request import Request, Response
from minion.routing import Router, SimpleMapper


class TestMinion(TestCase):
    def test_it_routes_simple_views(self):
        minion = Application(router=Router(mapper=SimpleMapper()))

        @minion.route(b"/show")
        def show(request):
            return Response(b"Hello World!")

        response = minion.serve(Request(url=URL(path=b"/show")), path=b"/show")
        self.assertEqual(response, Response(b"Hello World!"))


class RequestIntegrationTestMixin(object):
    def setUp(self):
        self.minion = Application()

        @self.minion.route(b"/respond", renderer=JSON())
        def respond(request):
            url = {
                attr.init_aliaser(attr.name) : getattr(request.url, attr.name)
                for attr in request.url.characteristic_attributes
            }
            return {"url" : url}

    def get_request(self, *args, **kwargs):
        kwargs.setdefault("headers", Headers())
        response = json.loads(self.get(*args, **kwargs))
        response["url"] = URL(**response["url"])
        return Request(**response)

    def test_it_parses_the_url(self):
        request = self.get_request(
            b"/respond?foo=bar#baz",
            headers=Headers([(b"Host", [b"example.com"])]),
        )
        self.assertEqual(
            request.url, URL(
                scheme=b"http",
                host=b"example.com",
                path=b"/respond",
                query={b"foo" : [b"bar"]},
                fragment=b"",  # Fragments should be ignored by servers.
            ),
        )
