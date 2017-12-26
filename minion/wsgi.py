from cached_property import cached_property as calculated_once
from future.moves.urllib.parse import parse_qsl
from future.utils import iteritems
from hyperlink import URL

from minion.http import Accept, Headers


class Request(object):
    def __init__(self, environ):
        self.environ = environ

    @calculated_once
    def accept(self):
        return Accept.from_header(header=self.environ.get("HTTP_ACCEPT"))

    @calculated_once
    def headers(self):
        return Headers(
            (name[5:].replace("_", "-"), [value])
            for name, value in iteritems(self.environ)
            if name.startswith("HTTP_")
        )

    @calculated_once
    def content(self):
        return self.environ["wsgi.input"]

    @calculated_once
    def method(self):
        return self.environ["REQUEST_METHOD"]

    @calculated_once
    def url(self):
        environ = self.environ
        host = environ.get("HTTP_HOST") or environ["SERVER_NAME"]
        path = environ.get("SCRIPT_NAME", "") + environ.get("PATH_INFO", "")
        return URL(
            host=host.decode("ascii"),
            port=int(environ["SERVER_PORT"]),
            path=path.lstrip("/").decode("ascii").split(u"/"),
            query=[
                (k.decode("ascii"), v.decode("ascii"))
                for k, v in parse_qsl(environ.get("QUERY_STRING", ""))
            ],
            scheme=environ["wsgi.url_scheme"].decode("ascii"),
        )


def create_app(application, request_class=Request):
    """
    Create a WSGI application out of the given Minion app.

    Arguments:

        application (Application):

            a minion app

        request_class (callable):

            a class to use for constructing incoming requests out of the WSGI
            environment. It will be passed a single arg, the environ.

            By default, this is :class:`minion.request.WSGIRequest` if
            unprovided.
    """

    def wsgi(environ, start_response):
        response = application.serve(
            request=request_class(environ),
            path=environ.get("PATH_INFO", ""),
        )
        start_response(
            response.status, [
                (name, b",".join(values))
                for name, values in response.headers.canonicalized()
            ],
        )
        return [response.content]
    return wsgi
