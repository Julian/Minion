"""
APIs for storing and retrieving HTTP headers and cookies.

"""

from bisect import insort

from future.utils import iteritems, viewkeys
from pyrsistent import m
import attr


_CANONICAL_HEADER_NAMES = {
    b"content-md5": b"Content-MD5",
    b"dnt": b"DNT",
    b"etag": b"ETag",
    b"p3p": b"P3P",
    b"te": b"TE",
    b"www-authenticate": b"WWW-Authenticate",
    b"x-xss-protection": b"X-XSS-Protection",
}
DEFAULT_PORTS = {b"http": 80, b"https": 443}


class NoSuchHeader(LookupError):
    """
    An operation on a non-present or -existing HTTP header was performed.

    """


class Headers(object):
    def __init__(self, contents=()):
        self._contents = dict(
            (name.lower(), values) for name, values in contents
        )

    def __contains__(self, name):
        return name.lower() in self._contents

    def __getitem__(self, name):
        try:
            return self._contents[name.lower()]
        except KeyError:
            raise NoSuchHeader(name)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._contents == other._contents

    def __ne__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return not self == other

    def __hash__(self):
        calculated = getattr(self, "_hash", None)
        if calculated is None:
            calculated = 0
            for name, values in iteritems(self._contents):
                calculated ^= hash((name, tuple(values)))
            self._hash = calculated
        return calculated

    def __repr__(self):
        contents = " ".join(
            "{0}={1!r}".format(name, values)
            for name, values in sorted(self.canonicalized())
        )
        return "<{.__class__.__name__} contents={{{}}}>".format(self, contents)

    def canonicalized(self):
        for name, values in iteritems(self._contents):
            canonical_name = _CANONICAL_HEADER_NAMES.get(name)
            if canonical_name is None:
                canonical_name = b"-".join(
                    word.capitalize() for word in name.split(b"-")
                )
            yield canonical_name, values

    def get(self, name, default=None):
        return self._contents.get(name.lower(), default)


class MutableHeaders(Headers):

    __hash__ = None

    def __setitem__(self, name, values):
        self._contents[name.lower()] = values

    def add_value(self, name, value):
        existing = self.get(name)
        if existing is None:
            self[name] = [value]
        else:
            existing.append(value)

    def get(self, name, default=None):
        return self._contents.get(name.lower(), default)

    def pop(self, name, *args, **kwargs):
        try:
            return self._contents.pop(name.lower(), *args, **kwargs)
        except KeyError:
            raise NoSuchHeader(name)


@attr.s
class Accept(object):
    """
    A parsed representation of an HTTP Accept header (see :rfc:`7231#5.3.2`\ ).

    """

    media_types = attr.ib()

    @classmethod
    def from_header(cls, header):
        """
        Parse out an Accept header.

        """

        if header is None:
            return cls.ALL

        media_types = []
        for range_and_parameters in header.split(b","):
            raw_range, _, raw_parameters = range_and_parameters.partition(b";")

            quality = 1.0
            media_parameters = {}
            if raw_parameters:
                for raw_parameter in raw_parameters.split(b";"):
                    key, _, value = raw_parameter.partition(b"=")
                    key = key.strip()
                    value = value.strip()
                    if key == b"q":
                        quality = float(value)
                    else:
                        media_parameters[key] = value

            raw_type, _, raw_subtype = raw_range.partition(b"/")

            type = raw_type.strip()
            subtype = raw_subtype.strip()

            insort(
                media_types,
                MediaRange(
                    type=type if type != b"*" else STAR,
                    subtype=subtype if subtype != b"*" else STAR,
                    quality=quality,
                    parameters=media_parameters,
                ),
            )
        return cls(media_types=tuple(media_types))


class _Star(object):
    """
    An open media range value.

    """

    def __lt__(self, other):
        return True

    def __repr__(self):
        return "*"


STAR = _Star()


@attr.s(cmp=False, hash=True)
class MediaRange(object):
    """
    A media range.

    Open ranges (e.g. ``text/*`` or ``*/*``\ ) are represented by
    :attr:`type` and / or :attr:`subtype` being ``None``\ .

    """

    type = attr.ib(default=STAR)
    subtype = attr.ib(default=STAR)
    parameters = attr.ib(default=m())
    quality = attr.ib(default=1.0)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return attr.astuple(self) == attr.astuple(other)

    def __ne__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return not self == other

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        if self.quality < other.quality:
            return True
        elif self.quality > other.quality:
            return False

        if self.type != other.type:
            return self.type is STAR

        if self.subtype != other.subtype:
            return self.subtype is STAR

        return viewkeys(self.parameters) < viewkeys(other.parameters)


Accept.ALL = Accept(media_types=(MediaRange(),))


def _vars(instance):
    for attr in instance.characteristic_attributes:
        name = attr.name
        yield attr.init_aliaser(name), getattr(instance, name)


def _replace(instance, **new):
    for name, value in _vars(instance):
        if name not in new:
            new[name] = value
    return instance.__class__(**new)
