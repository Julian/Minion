from minion import Application, Response
from minion.compat import StringIO
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

    def test_render(self):
        @self.minion.route("/foo/bar")
        def foo_bar(request):
            self.assertEqual(request.headers.get(b"X-Foo"), [b"Hello"])
            return Response(
                code=302,
                content=request.path,
                headers=Headers([(b"Location", [b"http://example.com"])]),
            )

        request = FakeRequest(uri="/bla/foo/bar", postpath=["foo", "bar"])
        request.requestHeaders.setRawHeaders(b"X-Foo", [b"Hello"])
        response = render(resource=self.resource, request=request)
        self.assertRedirected(
            request, response, "http://example.com", content="/foo/bar",
        )

    def test_interface(self):
        verifyObject(IResource, self.resource)


# Copied from https://tm.tl/5527
def render(resource, request):
    result = resource.render(request)
    if isinstance(result, str):
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
    def __init__(self, uri, postpath, method="GET"):
        server.Request.__init__(self, DummyChannel(), False)
        self.written = StringIO()
        self.content = StringIO()
        self.method = method
        self.uri = uri
        self.postpath = postpath

    def write(self, data):
        self.written.write(data)
