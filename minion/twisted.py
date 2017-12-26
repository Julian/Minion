from __future__ import absolute_import

from hyperlink import URL
from twisted.web.resource import IResource
from zope.interface import implementer

from minion.http import Headers
from minion.request import Request


@implementer(IResource)
class MinionResource(object):
    """
    Wrap a Minion application in a :class:`twisted.web.resource.IResource`\ .

    Arguments:

        application (Application):

            a minion app
    """

    isLeaf = True

    def __init__(self, application):
        self.application = application

    def getChildWithDefault(self, path, request):
        return self

    def putChild(self, path, child):
        raise NotImplementedError()

    def render(self, twistedRequest):
        path = twistedRequest.uri.lstrip("/").decode("ascii").split(u"/")
        request = Request(
            content=twistedRequest.content,
            headers=Headers(twistedRequest.requestHeaders.getAllRawHeaders()),
            method=twistedRequest.method,
            url=URL(
                scheme=u"https" if twistedRequest.isSecure() else u"http",
                host=twistedRequest.getRequestHostname().decode("ascii"),
                path=path,
                query=[
                    (k.decode("ascii"), each.decode("ascii"))
                    for k, v in twistedRequest.args.items()
                    for each in v
                ],
            ),
        )
        response = self.application.serve(
            request=request, path=b"/" + b"/".join(twistedRequest.postpath),
        )

        twistedRequest.setResponseCode(response.code)

        for k, v in response.headers.canonicalized():
            twistedRequest.responseHeaders.setRawHeaders(k, v)

        return response.content
