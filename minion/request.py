from __future__ import absolute_import
from io import BytesIO

from cached_property import cached_property as calculated_once
from future.utils import iteritems
from werkzeug.http import HTTP_STATUS_CODES as HTTP_STATUS_PHRASES
import attr

from minion.deferred import Deferred
from minion.http import Accept, Headers, MutableHeaders


HTTP_STATUS_CODES = dict(
    (code, "{0} {1}".format(code, phrase))
    for code, phrase in iteritems(HTTP_STATUS_PHRASES)
)


class Responder(object):
    """
    A responder represents a pending HTTP response for a corresponding request.

    """

    def __init__(self, request):
        self._after_deferreds = []
        self.request = request

    def after(self):
        """
        Return a deferred that will fire after the request is finished.

        Returns:

            Deferred: a new deferred that will fire appropriately

        """

        d = Deferred()
        self._after_deferreds.append(d)
        return d.chain

    def finish(self):
        for d in self._after_deferreds:
            d.succeed(self)


class Manager(object):
    """
    The request manager coordinates state during each active request.

    """

    def __init__(self):
        self._requests = {}

    def after_response(self, request, fn, *args, **kwargs):
        """
        Call the given callable after the given request has its response.

        Arguments:

            request:

                the request to piggyback

            fn (callable):

                a callable that takes at least two arguments, the request and
                the response (in that order), along with any additional
                positional and keyword arguments passed to this function which
                will be passed along. If the callable returns something other
                than ``None``, it will be used as the new response.
        """

        self._requests[id(request)]["callbacks"].append((fn, args, kwargs))

    def request_started(self, request):
        self._requests[id(request)] = {"callbacks": [], "assets": {}}

    def request_served(self, request, response):
        request_data = self._requests.pop(id(request))
        for callback, args, kwargs in request_data["callbacks"]:
            callback_response = callback(response, *args, **kwargs)
            if callback_response is not None:
                response = callback_response
        return response


@attr.s
class Request(object):

    url = attr.ib()
    content = attr.ib(default=attr.Factory(BytesIO))
    headers = attr.ib(default=attr.Factory(Headers))
    method = attr.ib(default=b"GET")
    messages = attr.ib(default=attr.Factory(list), cmp=False)

    @calculated_once
    def accept(self):
        header = self.headers.get("Accept")
        if header is not None:
            header = ",".join(header)
        return Accept.from_header(header=header)

    def flash(self, message):
        self.messages.append(_Message(content=message))


@attr.s
class Response(object):

    content = attr.ib(default="")
    code = attr.ib(default=200)
    headers = attr.ib(default=attr.Factory(MutableHeaders))

    @property
    def status(self):
        return HTTP_STATUS_CODES[self.code]


@attr.s
class _Message(object):
    """
    A flashed message.

    """

    content = attr.ib()


def redirect(to, code=302):
    """
    Return a redirect response to the given URL.

    """

    return Response(headers=MutableHeaders([("Location", [to])]), code=code)
