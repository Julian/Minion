from functools import partial
import json

from characteristic import Attribute, attributes

from minion import Response


class JSON(object):
    def __init__(self, **kwargs):
        self._dumps = partial(json.dumps, **kwargs)

    def render(self, jsonable):
        return Response(self._dumps(jsonable))


@attributes(
    [
        Attribute(name="encoding"),
        Attribute(name="errors", default_value="strict"),
    ],
)
class Unicode(object):
    def render(self, text):
        return Response(
            text.encode(encoding=self.encoding, errors=self.errors),
        )


UTF8 = Unicode(encoding="utf-8")
