"""
APIs for storing and retrieving HTTP headers and cookies.

"""

from bisect import insort

from cached_property import cached_property as calculated_once
from characteristic import Attribute, attributes
from future.moves.urllib.parse import parse_qs, unquote, unquote_plus
from future.utils import iteritems, viewkeys


_CANONICAL_HEADER_NAMES = {
    b"content-md5": b"Content-MD5",
    b"dnt": b"DNT",
    b"etag": b"ETag",
    b"p3p": b"P3P",
    b"te": b"TE",
    b"www-authenticate": b"WWW-Authenticate",
    b"x-xss-protection": b"X-XSS-Protection",
}


class NoSuchHeader(LookupError):
    """
    An operation on a non-present or -existing HTTP header was performed.

    """


class InvalidURL(LookupError):
    """
    Parsing resulted in an invalid URL.

    """


@attributes(
    [
        Attribute(name="scheme", default_value=b""),
        Attribute(name="username", default_value=b""),
        Attribute(name="password", default_value=b""),
        Attribute(name="host", default_value=b""),
        Attribute(name="port", default_value=None),
        Attribute(name="path", default_value=b""),
        Attribute(name="query", default_factory=dict),
        Attribute(name="fragment", default_value=b""),
        Attribute(
            name="_unnormalized",
            default_value=None,
            exclude_from_cmp=True,
        ),
        Attribute(
            name="unnormalized_scheme",
            default_value=None,
            exclude_from_cmp=True,
        ),
    ],
)
class URL(object):
    def __init__(self, authority=None, userinfo=None):
        if authority is not None:
            self.authority = authority
        if userinfo is not None:
            self.userinfo = userinfo

    @classmethod
    def from_bytes(cls, bytes):
        """
        Parse a URL from some bytes.

        """

        scheme, _, rest = bytes.strip().partition(b":")

        if scheme and not rest.startswith(b"//"):
            raise InvalidURL("{!r} is not a valid URL".format(bytes))

        authority, slash, rest = rest[2:].partition(b"/")
        userinfo, _, host_and_port = authority.rpartition(b"@")
        username, _, password = userinfo.partition(b":")
        host, _, port_str = host_and_port.partition(b":")

        if not port_str:
            port = None
        else:
            try:
                port = int(unquote(port_str))
            except ValueError:
                raise InvalidURL("{!r} is not a valid port".format(port_str))

        path, _, rest = rest.partition(b"?")
        query, _, fragment = rest.partition(b"#")

        return cls.normalized(
            scheme=scheme,
            username=username,
            password=password,
            host=host,
            port=port,
            path=unquote(slash + path),
            query=parse_qs(query),
            fragment=unquote_plus(fragment),
            unnormalized=bytes,
            authority=authority,
            userinfo=userinfo,
        )

    @classmethod
    def normalized(cls, scheme, **kwargs):
        return cls(
            unnormalized_scheme=scheme,
            scheme=scheme.lower(),
            **kwargs
        )

    @calculated_once
    def authority(self):
        return "{self.userinfo}@{self.host}:{self.port}".format(self=self)

    @calculated_once
    def userinfo(self):
        return "{self.username}:{self.password}".format(self=self)

    def to_bytes(self):
        url = self._unnormalized
        if url is not None:
            return url
        url = self._unnormalized = (
            "{self.scheme}://{self.authority}{self.path}?{self.query}#{self.fragment}".format(self=self)
        )
        return url


class Headers(object):
    def __init__(self, contents=()):
        self._contents = dict(
            (name.lower(), values) for name, values in contents
        )

    def __contains__(self, name):
        return name.lower() in self._contents

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
    def add_value(self, name, value):
        existing = self.get(name)
        if existing is None:
            self.set(name, [value])
        else:
            existing.append(value)

    def get(self, name, default=None):
        return self._contents.get(name.lower(), default)

    def set(self, name, values):
        self._contents[name.lower()] = values

    def discard(self, name):
        self._contents.pop(name.lower(), None)

    def remove(self, name):
        try:
            del self._contents[name.lower()]
        except KeyError:
            raise NoSuchHeader(name)


@attributes(
    [
        Attribute(name="media_types"),
    ],
)
class Accept(object):
    """
    A parsed representation of an HTTP Accept header (see :rfc:`7231#5.3.2`\ ).

    """

    @classmethod
    def from_header(cls, header):
        """
        Parse out an Accept header.

        """

        if header is None:
            return cls.ALL

        media_types = []
        for range_and_parameters in header.split(","):
            raw_range, _, raw_parameters = range_and_parameters.partition(";")

            quality = 1.0
            media_parameters = {}
            if raw_parameters:
                for raw_parameter in raw_parameters.split(";"):
                    key, _, value = raw_parameter.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if key == "q":
                        quality = float(value)
                    else:
                        media_parameters[key] = value

            raw_type, _, raw_subtype = raw_range.partition("/")

            type = raw_type.strip()
            subtype = raw_subtype.strip()

            insort(
                media_types,
                MediaRange(
                    type=type if type != "*" else STAR,
                    subtype=subtype if subtype != "*" else STAR,
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


@attributes(
    [
        Attribute(name="type", default_value=STAR),
        Attribute(name="subtype", default_value=STAR),
        Attribute(name="parameters", default_factory=dict),
        Attribute(name="quality", default_value=1.0),
    ],
    apply_with_cmp=False,
)
class MediaRange(object):
    """
    A media range.

    Open ranges (e.g. ``text/*`` or ``*/*``\ ) are represented by
    :attr:`type` and / or :attr:`subtype` being ``None``\ .

    """

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return all(
            getattr(self, attribute.name) == getattr(other, attribute.name)
            for attribute in self.characteristic_attributes
        )

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

    def __hash__(self):
        values = tuple(
            getattr(self, attr.name)
            for attr in self.characteristic_attributes
            if attr.name != "parameters"
        )
        return hash(values + tuple(self.parameters.items()))


Accept.ALL = Accept(media_types=(MediaRange(),))
