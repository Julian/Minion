from functools import partial, wraps
import json

from characteristic import Attribute, attributes

from minion.http import Headers, MediaRange
from minion.request import Response


class JSON(object):
    """
    An 'intelligent' JSON renderer that pretty-prints JSON for humans.

    """

    def __init__(self, **kwargs):
        self._dumps = partial(json.dumps, **kwargs)

    def render(self, request, jsonable):
        machine_json = request.accept.media_types[-1] == MediaRange(
            type="application", subtype="json",
        )
        if machine_json:
            content = self._dumps(jsonable, separators=",:")
        else:
            content = self._dumps(jsonable, indent=2, sort_keys=True)
        return Response(
            content=content,
            headers=Headers([("Content-Type", ["application/json"])]),
        )


class SimpleJSON(object):
    """
    A simple JSON renderer that renders by dumping with any given parameters.

    """

    def __init__(self, **kwargs):
        self._dumps = partial(json.dumps, **kwargs)

    def render(self, request, jsonable):
        return Response(self._dumps(jsonable))


@attributes(
    [
        Attribute(name="encoding"),
        Attribute(name="errors", default_value="strict"),
    ],
)
class Unicode(object):
    def render(self, request, text):
        return Response(
            text.encode(encoding=self.encoding, errors=self.errors),
        )


UTF8 = Unicode(encoding="utf-8")


def bind(renderer, to):
    """
    Bind a renderer to the given callable by constructing a new rendering view.

    """

    @wraps(to)
    def view(request, **kwargs):
        try:
            returned = to(request, **kwargs)
        except Exception as error:
            view_error = getattr(renderer, "view_error", None)
            if view_error is None:
                raise
            return view_error(request, error)

        try:
            return renderer.render(request, returned)
        except Exception as error:
            render_error = getattr(renderer, "render_error", None)
            if render_error is None:
                raise
            return render_error(request, returned, error)

    return view
