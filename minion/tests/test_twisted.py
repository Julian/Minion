from unittest import skipIf

from future.moves.urllib.parse import parse_qs
from future.utils import PY3
from klein.test_resource import _render as render, requestMock as _requestMock
from twisted.trial.unittest import SynchronousTestCase
from twisted.web.resource import IResource
from zope.interface.verify import verifyObject

from minion.core import Application
from minion.http import Headers
from minion.request import Response
from minion.tests.test_integration import RequestIntegrationTestMixin
from minion.twisted import MinionResource


class TestMinionResource(SynchronousTestCase):
    def setUp(self):
        self.minion = Application()
        self.resource = MinionResource(self.minion)

    def assertRedirected(self, request, response, url, content=None):
        self.assertEqual(request.code, 302)
        self.assertEqual(
            request.responseHeaders.getRawHeaders("Location"), [url],
        )

        if content is not None:
            self.assertEqual(content, request.getWrittenData())

    @skipIf(PY3, "twisted.web doesn't support Py3 yet")
    def test_render(self):
        @self.minion.route(b"/foo/bar")
        def fooBar(request):
            self.assertEqual(request.headers.get(b"X-Foo"), [b"Hello"])
            return Response(
                code=302,
                content=request.url.path,
                headers=Headers([(b"Location", [b"http://example.com"])]),
            )

        request = makeRequest(
            path=b"/foo/bar", headers={b"X-Foo" : [b"Hello"]},
        )
        response = render(resource=self.resource, request=request)
        self.assertRedirected(
            request, response, b"http://example.com", content=b"/foo/bar",
        )

    @skipIf(PY3, "twisted.web doesn't support Py3 yet")
    def test_request_body(self):
        @self.minion.route(b"/")
        def respond(request):
            return Response(content=request.content.read())

        request = makeRequest(path=b"/", body=b"Hello world")
        render(resource=self.resource, request=request)
        self.assertEqual(request.getWrittenData(), b"Hello world")

    def test_interface(self):
        verifyObject(IResource, self.resource)


class TestRequestIntegration(RequestIntegrationTestMixin, SynchronousTestCase):
    def get(self, url, headers):
        request = makeRequest(path=url, headers=dict(headers.canonicalized()))
        render(resource=MinionResource(self.minion), request=request)
        return request.getWrittenData()

    def test_it_properly_routes_when_mounted_on_a_subpath(self):
        self.minion.route(b"/hello")(lambda request : Response(b"World"))
        request = makeRequest(path=b"/minion/hello")
        request.prepath.append(request.postpath.pop(0))
        render(resource=MinionResource(self.minion), request=request)
        self.assertEqual(request.getWrittenData(), b"World")


def makeRequest(path, *args, **kwargs):
    """
    Wrap Klein's request mock to support query strings and host headers.

    """

    path, _, queryString = path.partition(b"?")
    request = _requestMock(path=path, *args, **kwargs)
    request.args = parse_qs(queryString.rpartition(b"#")[0])

    # klein has a bug where it overrides the host when you call requestMock
    host = kwargs.get("headers", {}).get(b"Host", [b"localhost"])[0]
    request.setHost(host, kwargs.get("port", 80))

    return request
