from characteristic import Attribute, attributes

from minion import Response


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
