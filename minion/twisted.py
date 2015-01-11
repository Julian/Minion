from __future__ import absolute_import

from twisted.web.resource import IResource
from zope.interface import implementer

from minion.http import Headers, URL
from minion.request import Request


@implementer(IResource)
class MinionResource(object):
    """
    Wrap a Minion application in a :class:`twisted.web.resource.IResource`\ .

    :argument Application application: a minion app

    """

    isLeaf = True

    def __init__(self, application):
        self.application = application

    def getChildWithDefault(self, path, request):
        return self

    def putChild(self, path, child):
        raise NotImplementedError()

    def render(self, twistedRequest):
        request = Request(
            content=twistedRequest.content,
            headers=Headers(twistedRequest.requestHeaders.getAllRawHeaders()),
            method=twistedRequest.method,
            url=URL(
                scheme=b"https" if twistedRequest.isSecure() else b"http",
                host=twistedRequest.getRequestHostname(),
                path=twistedRequest.uri,
                query=twistedRequest.args,
            ),
        )
        response = self.application.serve(
            request=request, path=b"/" + b"/".join(twistedRequest.postpath),
        )

        twistedRequest.setResponseCode(response.code)

        for k, v in response.headers.canonicalized():
            twistedRequest.responseHeaders.setRawHeaders(k, v)

        return response.content
