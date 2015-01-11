from cached_property import cached_property as calculated_once
from future.moves.urllib.parse import parse_qs
from future.utils import iteritems

from minion.http import Accept, Headers, URL


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
        return URL.normalized(
            host=environ.get("HTTP_HOST") or environ["SERVER_NAME"],
            port=int(environ["SERVER_PORT"]),
            path=environ.get("SCRIPT_NAME", "") + environ.get("PATH_INFO", ""),
            query=parse_qs(environ.get("QUERY_STRING", "")),
            scheme=environ["wsgi.url_scheme"],
        )


def create_app(application, request_class=Request):
    """
    Create a WSGI application out of the given Minion app.

    :argument Application application: a minion app
    :argument request_class: a class to use for constructing incoming requests
        out of the WSGI environment. It will be passed a single arg, the
        environ. By default, this is :class:`minion.request.WSGIRequest` if
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
