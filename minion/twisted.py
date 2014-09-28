from __future__ import absolute_import

from twisted.web.resource import IResource
from zope.interface import implementer

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

    def render(self, twisted_request):
        request = Request(
            method=twisted_request.method,
            path=twisted_request.uri,
        )
        response = self.application.serve(request)

        twisted_request.setResponseCode(response.code)

        for k, v in response.headers.iteritems():  # XXX
            twisted_request.responseHeaders.setRawHeaders(k, [v])

        return response.content
