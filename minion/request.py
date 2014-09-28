from twisted.internet.defer import Deferred
from werkzeug.http import HTTP_STATUS_CODES as HTTP_STATUS_PHRASES

from minion.compat import iteritems


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

        :returns: a new :class:`twisted.internet.defer.Deferred` for each call
            to this function.

        """

        d = Deferred()
        self._after_deferreds.append(d)
        return d

    def finish(self):
        for d in self._after_deferreds:
            d.callback(self)


class Manager(object):
    """
    The request manager coordinates state during each active request.

    """

    def __init__(self):
        self.requests = {}

    def after_response(self, request, fn, *args, **kwargs):
        """
        Call the given callable after the given request has its response.

        :argument request: the request to piggyback
        :argument fn: a callable that takes at least two arguments, the request
            and the response (in that order), along with any additional
            positional and keyword arguments passed to this function which will
            be passed along. If the callable returns something other than
            ``None``, it will be used as the new response.

        """

        self.requests[request]["callbacks"].append((fn, args, kwargs))

    def request_started(self, request):
        self.requests[request] = {"callbacks": [], "resources": {}}

    def request_served(self, request, response):
        request_data = self.requests.pop(request)
        for callback, args, kwargs in request_data["callbacks"]:
            callback_response = callback(response, *args, **kwargs)
            if callback_response is not None:
                response = callback_response
        return response


class Request(object):
    def __init__(self, path, method="GET"):
        self.messages = []
        self.method = method
        self.path = path

    def __repr__(self):
        return "<{self.__class__.__name__} {self.path!r}>".format(self=self)

    def flash(self, message):
        self.messages.append(_Message(content=message))


class WSGIRequest(object):
    def __init__(self, environ):
        self.environ = environ

    @property
    def method(self):
        return self.environ["REQUEST_METHOD"]

    @property
    def path(self):
        return self.environ["PATH_INFO"]


class Response(object):
    def __init__(self, content="", code=200, headers=None):
        if headers is None:
            headers = {}

        self.code = code
        self.content = content
        self.headers = headers

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.content == other.content

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "<{self.__class__.__name__} {self.content!r}>".format(self=self)

    @property
    def status(self):
        return HTTP_STATUS_CODES[self.code]


class _Message(object):
    """
    A flashed message.

    """

    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return "<{self.__class__.__name__} content={self.content!r}>".format(
            self=self,
        )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.content == other.content

    def __ne__(self, other):
        return not self == other
