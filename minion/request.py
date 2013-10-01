from werkzeug.http import HTTP_STATUS_CODES as HTTP_STATUS_PHRASES

from minion.compat import iteritems


HTTP_STATUS_CODES = dict(
    (code, "{0} {1}".format(code, phrase))
    for code, phrase in iteritems(HTTP_STATUS_PHRASES)
)


class Request(object):
    def __init__(self, path, method="GET"):
        self.method = method
        self.path = path

    def __repr__(self):
        return "<{self.__class__.__name__} {self.path!r}>".format(self=self)


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

    default_code = 200

    def __init__(self, content="", code=None, headers=None):
        self.content = content

        if code is None:
            code = self.default_code
        self.code = code

        if headers is None:
            headers = {}
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
