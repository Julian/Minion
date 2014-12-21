from unittest import skipIf

from minion import Application, Response
from minion.compat import BytesIO, PY3
from minion.http import Headers
from minion.twisted import MinionResource

from twisted.internet.defer import succeed
from twisted.trial.unittest import SynchronousTestCase
from twisted.web import server
from twisted.web.resource import IResource
from twisted.web.test.test_web import DummyChannel
from zope.interface.verify import verifyObject


class TestMinionResource(SynchronousTestCase):
    def setUp(self):
        self.minion = Application()
        self.resource = MinionResource(self.minion)

    def assertRedirected(self, request, response, url, content=None):
        result = self.successResultOf(response)

        self.assertEqual(request.code, 302)
        self.assertEqual(
            request.responseHeaders.getRawHeaders("Location"), [url],
        )

        if content is not None:
            self.assertEqual(result, content)

    @skipIf(PY3, "twisted.web doesn't support Py3 yet")
    def test_render(self):
        @self.minion.route(b"/foo/bar")
        def foo_bar(request):
            self.assertEqual(request.headers.get(b"X-Foo"), [b"Hello"])
            return Response(
                code=302,
                content=request.path,
                headers=Headers([(b"Location", [b"http://example.com"])]),
            )

        request = FakeRequest(uri=b"/bla/foo/bar", postpath=[b"foo", b"bar"])
        request.requestHeaders.setRawHeaders(b"X-Foo", [b"Hello"])
        response = render(resource=self.resource, request=request)
        self.assertRedirected(
            request, response, b"http://example.com", content=b"/foo/bar",
        )

    @skipIf(PY3, "twisted.web doesn't support Py3 yet")
    def test_request_body(self):
        @self.minion.route(b"/")
        def respond(request):
            return Response(content=request.content.read())

        request = FakeRequest(uri=b"/", content=b"Hello world")
        response = self.successResultOf(
            render(resource=self.resource, request=request),
        )
        self.assertEqual(response, b"Hello world")

    def test_interface(self):
        verifyObject(IResource, self.resource)


# Copied from https://tm.tl/5527
def render(resource, request):
    result = resource.render(request)
    if isinstance(result, bytes):
        request.write(result)
        request.finish()
        return succeed(request.written.getvalue())
    elif result is server.NOT_DONE_YET:
        if request.finished:
            return succeed(request.written.getvalue())
        else:
            d = request.notifyFinish()
            d.addCallback(lambda _: request.written.getvalue())
            return d
    else:
        raise ValueError("Unexpected return value: %r" % (result,))


class FakeRequest(server.Request):
    def __init__(self, uri, postpath=(), method=b"GET", content=b""):
        server.Request.__init__(self, DummyChannel(), False)
        self.written = BytesIO()
        self.content = BytesIO(content)
        self.method = method
        self.uri = uri
        self.postpath = list(postpath)

    def write(self, data):
        self.written.write(data)
