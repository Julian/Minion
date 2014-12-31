from unittest import TestCase

from future.utils import PY3
from testscenarios import with_scenarios

from minion import http


class TestURL(TestCase):
    def test_to_bytes_all_components(self):
        url = http.URL(
            scheme="http",
            username="user",
            password="password",
            host="example.com",
            port=8080,
            path="/path",
            query="query=value",
            fragment="fragment",
        )
        self.assertEqual(
            url.to_bytes(),
            "http://user:password@example.com:8080/path?query=value#fragment",
        )


class TestURLCompoundComponents(TestCase):
    def test_authority(self):
        url = http.URL(
            scheme="http",
            username="user",
            password="password",
            host="example.com",
            port=8080,
            path="/path",
            query="query=value",
            fragment="fragment",
        )
        self.assertEqual(url.authority, "user:password@example.com:8080")

    def test_authority_no_user(self):
        url = http.URL(
            scheme="http", password="pass", host="example.com", port=8080,
        )
        self.assertEqual(url.authority, ":pass@example.com:8080")

    def test_authority_no_password(self):
        url = http.URL(
            scheme="http", username="user", host="example.com", port=8080,
        )
        self.assertEqual(url.authority, "user@example.com:8080")

    def test_authority_no_userinfo(self):
        url = http.URL(scheme="http", host="example.com", port=8080)
        self.assertEqual(url.authority, "example.com:8080")

    def test_authority_from_bytes(self):
        url = http.URL.from_bytes("https://foo:bar@example.org:4443/path")
        self.assertEqual(url.authority, "foo:bar@example.org:4443")

    def test_authority_from_bytes_no_user(self):
        url = http.URL.from_bytes("https://:bar@example.org:4443/path")
        self.assertEqual(url.authority, ":bar@example.org:4443")

    def test_authority_from_bytes_no_password(self):
        url = http.URL.from_bytes("https://foo@example.org:4443/path")
        self.assertEqual(url.authority, "foo@example.org:4443")

    def test_authority_from_bytes_no_userinfo(self):
        url = http.URL.from_bytes("https://example.org:4443/path")
        self.assertEqual(url.authority, "example.org:4443")

    def test_userinfo(self):
        url = http.URL(
            username="user",
            password="password",
            host="example.com",
            port=8080,
        )
        self.assertEqual(url.userinfo, "user:password")

    def test_userinfo_no_user(self):
        url = http.URL(password="pass", host="example.com", port=8080)
        self.assertEqual(url.userinfo, ":pass")

    def test_userinfo_no_password(self):
        url = http.URL(username="user", host="example.com", port=8080)
        self.assertEqual(url.userinfo, "user")

    def test_userinfo_from_bytes(self):
        url = http.URL.from_bytes("https://foo:bar@example.org:4443/path")
        self.assertEqual(url.userinfo, "foo:bar")

    def test_userinfo_from_bytes_no_user(self):
        url = http.URL.from_bytes("https://:bar@example.org:4443/path")
        self.assertEqual(url.userinfo, ":bar")

    def test_userinfo_from_bytes_no_password(self):
        url = http.URL.from_bytes("https://foo@example.org:4443/path")
        self.assertEqual(url.userinfo, "foo")


class TestURLNormalized(TestCase):
    def test_whitespace_is_stripped(self):
        """
        https://url.spec.whatwg.org/#url-parsing

        """

        url = http.URL.from_bytes(" \n http://example.com  \t ")
        self.assertEqual(url, http.URL.from_bytes("http://example.com"))

    def test_scheme_is_lowercased(self):
        """
        https://url.spec.whatwg.org/#scheme-start-state

        """

        url = http.URL.normalized(scheme=b"HTTP")
        self.assertEqual(url.scheme, b"http")
        self.assertEqual(url.unnormalized_scheme, b"HTTP")

    def test_scheme_already_lowercased(self):
        url = http.URL.normalized(scheme=b"http")
        self.assertEqual(url.scheme, b"http")
        self.assertEqual(url.unnormalized_scheme, b"http")


@with_scenarios()
class TestURLFromBytes(TestCase):

    scenarios = [
        (
            "quoting", {
                "url" : b"HTTP://example.com.:%38%30/%70a%74%68?a=%31#1%323",
                "expected" : {
                    "scheme" : b"HTTP",
                    "username" : b"",
                    "password" : b"",
                    "host" : b"example.com.",
                    "port" : 80,
                    "path" : b"/path",
                    "query" : {b"a" : [b"1"]},
                    "fragment" : b"123",
                },
            },
        ),
        (
            "credentials", {
                "url" : b"http://user:pass@example.com:8080/path?q=val#frag",
                "expected" : {
                    "scheme" : b"http",
                    "username" : b"user",
                    "password" : b"pass",
                    "host" : b"example.com",
                    "port" : 8080,
                    "path" : b"/path",
                    "query" : {b"q" : [b"val"]},
                    "fragment" : b"frag",
                },
            },
        ),
        (
            "no_path", {
                "url" : b"http://example.org:8080",
                "expected" : {
                    "scheme" : b"http",
                    "host" : b"example.org",
                    "port" : 8080,
                    "path" : b"",
                },
            },
        ),
        (
            "no_path_no_port", {
                "url" : b"http://example.org",
                "expected" : {
                    "scheme" : b"http",
                    "host" : b"example.org",
                    "path" : b"",
                },
            },
        ),
        (
            "empty", {
                "url" : b"",
                "expected" : {
                    "scheme" : b"",
                    "username" : b"",
                    "password" : b"",
                    "host" : b"",
                    "port" : None,
                    "path" : b"",
                    "query" : {},
                    "fragment" : b"",
                },
            },
        ),
    ]

    def test_from_bytes(self):
        self.assertEqual(
            http.URL.from_bytes(self.url),
            http.URL.normalized(**self.expected),
        )

    def test_roundtrip(self):
        self.assertEqual(http.URL.from_bytes(self.url).to_bytes(), self.url)


@with_scenarios()
class TestFromInvalidURLs(TestCase):

    scenarios = [
        (
            "with_invalid_port", {
                "url" : b"http://example.org:invalid",
                "message" : "'invalid' is not a valid port"
            },
        ),
        (
            "with_missing_slashes", {
                "url" : b"http:",
                "message" : "'http:' is not a valid URL"
            },
        ),
        (
            "with_missing_slash", {
                "url" : b"http:/",
                "message" : "'http:/' is not a valid URL"
            },
        ),
    ]

    def test_invalid_url(self):
        with self.assertRaises(http.InvalidURL) as e:
            http.URL.from_bytes(self.url)
        self.assertEqual(str(e.exception), self.message)


class HeaderRetrievalTestsMixin(object):
    """
    Test that headers can be retrieved from a populated Header instance.

    """

    def test_init(self):
        headers = self.Headers([(b"Foo", [b"Bar"])])
        self.assertEqual(headers.get(b"Foo"), [b"Bar"])

    def test_contains(self):
        headers = self.Headers([(b"test", [b"hello", b"world"])])
        self.assertIn(b"test", headers)

    def test_does_not_contain(self):
        headers = self.Headers()
        self.assertNotIn(b"test", headers)

    def test_get(self):
        headers = self.Headers([(b"thing", [b"value"])])
        self.assertEqual(headers.get(b"thing"), [b"value"])

    def test_get_with_default(self):
        headers = self.Headers()
        default = object()
        self.assertIs(headers.get(b"nonexisting", default), default)

    def test_get_defaults_to_None(self):
        headers = self.Headers()
        self.assertIsNone(headers.get(b"nonexisting"))

    def test_canonicalized(self):
        headers = self.Headers(
            [
                (b"red", [b"Blue"]),
                (b"yellow-and-green", [b"purple-too"]),
                (b"content-md5", [b"Stuff"]),
                (b"dnT", [b"0"]),
                (b"etAg", [b"more"]),
                (b"p3p", [b"stuff"]),
                (b"te", [b"things"]),
                (b"www-authenticate", [b"hooray"]),
                (b"x-xss-protection", [b"done"]),
            ],
        )

        self.assertEqual(
            sorted(headers.canonicalized()), [
                (b"Content-MD5", [b"Stuff"]),
                (b"DNT", [b"0"]),
                (b"ETag", [b"more"]),
                (b"P3P", [b"stuff"]),
                (b"Red", [b"Blue"]),
                (b"TE", [b"things"]),
                (b"WWW-Authenticate", [b"hooray"]),
                (b"X-XSS-Protection", [b"done"]),
                (b"Yellow-And-Green", [b"purple-too"]),
            ],
        )

    def test_eq(self):
        Headers = self.Headers
        self.assertTrue(
            Headers([(b"foo", [b"bar"])]) == Headers([(b"foo", [b"bar"])])
        )
        self.assertFalse(
            Headers([(b"foo", [b"bar"])]) == Headers([(b"foo", [])])
        )

    def test_ne(self):
        Headers = self.Headers
        self.assertTrue(
            Headers([(b"foo", [b"bar"])]) != Headers([(b"foo", [])])
        )
        self.assertFalse(
            Headers([(b"foo", [b"bar"])]) != Headers([(b"foo", [b"bar"])])
        )

    def test_eq_NotImplemented(self):
        self.assertFalse(self.Headers() == {})

    def test_ne_NotImplemented(self):
        self.assertTrue(self.Headers() != {})

    def test_repr(self):
        headers = self.Headers(
            [(b"foo", [b"bar"]), (b"thing", [b"baz", b"quux"])]
        )

        if PY3:
            fields = " contents={b'Foo'=[b'bar'] b'Thing'=[b'baz', b'quux']}>"
        else:
            fields = " contents={Foo=['bar'] Thing=['baz', 'quux']}>"

        self.assertEqual(repr(headers), "<" + self.Headers.__name__ + fields)

    def test_empty_repr(self):
        headers = self.Headers()
        self.assertEqual(
            repr(headers), "<" + self.Headers.__name__ + " contents={}>",
        )


class TestMutableHeaders(HeaderRetrievalTestsMixin, TestCase):

    Headers = http.MutableHeaders

    def test_mutated_contains(self):
        headers = self.Headers()
        self.assertNotIn(b"thing", headers)

        headers.set(b"Thing", [b"hello", b"world"])

        self.assertIn(b"thing", headers)
        self.assertEqual(headers.get(b"thing"), [b"hello", b"world"])

    def test_add_value(self):
        headers = self.Headers([(b"foo", [b"bar"])])
        headers.add_value(b"foo", b"baz")
        self.assertEqual(headers.get(b"foo"), [b"bar", b"baz"])

    def test_add_new_value(self):
        headers = self.Headers()
        headers.add_value(b"thing", b"value")
        self.assertEqual(headers.get(b"thing"), [b"value"])

    def test_discard(self):
        headers = self.Headers([(b"Foo", [b"bar"])])
        self.assertIn(b"foo", headers)

        headers.discard(b"fOo")

        self.assertNotIn(b"foo", headers)
        self.assertEqual(headers, self.Headers())

    def test_discard_nonexisting(self):
        headers = self.Headers()
        headers.discard(b"nonexisting")
        self.assertEqual(headers, self.Headers())

    def test_remove(self):
        headers = self.Headers([(b"Foo", [b"bar"])])
        self.assertIn(b"foo", headers)

        headers.remove(b"fOo")

        self.assertNotIn(b"foo", headers)
        self.assertEqual(headers, self.Headers())

    def test_remove_nonexisting(self):
        headers = self.Headers()
        with self.assertRaises(http.NoSuchHeader):
            headers.remove(b"nonexisting")

    def test_mutated_eq_ne(self):
        first = self.Headers([(b"foo", [b"bar"])])
        second = self.Headers()

        second.add_value(b"foo", b"bar")
        self.assertEqual(first, second)

        second.add_value(b"foo", b"baz")
        self.assertNotEqual(first, second)


class TestImmutableHeaders(HeaderRetrievalTestsMixin, TestCase):

    Headers = http.Headers

    def test_hash(self):
        some_headers = set(
            [self.Headers([(b"a", [b"b"])]), self.Headers([(b"a", [b"b"])])],
        )
        self.assertEqual(some_headers, set([self.Headers([(b"a", [b"b"])])]))

    def test_empty_hash(self):
        some_headers = set([self.Headers(), self.Headers()])
        self.assertEqual(some_headers, set([self.Headers()]))


class TestAccept(TestCase):
    def test_basic(self):
        accept = http.Accept.from_header(header="application/json")
        media_range = http.MediaRange(
            type="application", subtype="json", quality=1.0,
        )
        self.assertEqual(accept, http.Accept(media_types=(media_range,)))

    def test_multiple(self):
        accept = http.Accept.from_header(header="audio/*; q=0.2, audio/basic")
        media_types = (
            http.MediaRange(type="audio", quality=0.2),
            http.MediaRange(type="audio", subtype="basic", quality=1.0),
        )
        self.assertEqual(accept, http.Accept(media_types=media_types))

    def test_strips_spaces(self):
        accept = http.Accept.from_header(header=" text/* ; q=0.2 ,  text/foo")
        media_types = (
            http.MediaRange(type="text", quality=0.2),
            http.MediaRange(type="text", subtype="foo", quality=1.0),
        )
        self.assertEqual(accept, http.Accept(media_types=media_types))

    def test_more_elaborate(self):
        accept = http.Accept.from_header(
            header="text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c",
        )
        media_types = (
            http.MediaRange(type="text", subtype="plain", quality=0.5),
            http.MediaRange(type="text", subtype="x-dvi", quality=0.8),
            http.MediaRange(type="text", subtype="html"),
            http.MediaRange(type="text", subtype="x-c"),
        )
        self.assertEqual(accept, http.Accept(media_types=media_types))

    def test_override_with_more_specific_type(self):
        accept = http.Accept.from_header(
            header="text/*, text/plain, text/plain;format=flowed, */*",
        )
        media_types = (
            http.MediaRange(),
            http.MediaRange(type="text"),
            http.MediaRange(type="text", subtype="plain"),
            http.MediaRange(
                type="text", subtype="plain", parameters=dict(format="flowed"),
            ),
        )
        self.assertEqual(accept, http.Accept(media_types=media_types))

    def test_quality_factors(self):
        accept = http.Accept.from_header(
            header="text/*;q=0.3, text/html;q=0.7, text/html;level=1, "
                   "text/html;level=2;q=0.4, */*;q=0.5",
        )
        media_types = (
            http.MediaRange(type="text", quality=0.3),
            http.MediaRange(
                type="text",
                subtype="html",
                quality=0.4,
                parameters=dict(level="2"),
            ),
            http.MediaRange(quality=0.5),
            http.MediaRange(type="text", subtype="html", quality=0.7),
            http.MediaRange(
                type="text", subtype="html", parameters=dict(level="1"),
            ),
        )
        self.assertEqual(accept, http.Accept(media_types=media_types))

    def test_no_header(self):
        accept = http.Accept.from_header(header=None)
        self.assertEqual(accept, http.Accept.ALL)


class TestMediaRange(TestCase):
    def test_eq(self):
        self.assertTrue(
            http.MediaRange(type="text", subtype="plain", quality=0.5) ==
            http.MediaRange(type="text", subtype="plain", quality=0.5),
        )

    def test_eq_type(self):
        self.assertFalse(
            http.MediaRange(type="text", subtype="plain", quality=0.5) ==
            http.MediaRange(type="foo", subtype="plain", quality=0.5),
        )

    def test_eq_subtype(self):
        self.assertFalse(
            http.MediaRange(type="text", subtype="plain", quality=0.5) ==
            http.MediaRange(type="text", subtype="other", quality=0.5),
        )

    def test_eq_quality(self):
        self.assertFalse(
            http.MediaRange(type="text", subtype="plain", quality=0.5) ==
            http.MediaRange(type="text", subtype="plain", quality=0.8),
        )

    def test_eq_parameters(self):
        self.assertFalse(
            http.MediaRange(type="text", parameters={"a": "b"}) ==
            http.MediaRange(type="text", parameters={"a": "c"}),
        )

    def test_ne(self):
        self.assertFalse(
            http.MediaRange(type="text", subtype="plain", quality=0.5) !=
            http.MediaRange(type="text", subtype="plain", quality=0.5),
        )

    def test_ne_type(self):
        self.assertTrue(
            http.MediaRange(type="text", subtype="plain", quality=0.5) !=
            http.MediaRange(type="foo", subtype="plain", quality=0.5),
        )

    def test_ne_subtype(self):
        self.assertTrue(
            http.MediaRange(type="text", subtype="plain", quality=0.5) !=
            http.MediaRange(type="text", subtype="other", quality=0.5),
        )

    def test_ne_quality(self):
        self.assertTrue(
            http.MediaRange(type="text", subtype="plain", quality=0.5) !=
            http.MediaRange(type="text", subtype="plain", quality=0.8),
        )

    def test_ne_parameters(self):
        self.assertTrue(
            http.MediaRange(type="text", parameters={"a": "b"}) !=
            http.MediaRange(type="text", parameters={"a": "c"}),
        )

    def test_lt_same_type_and_subtype(self):
        self.assertLess(
            http.MediaRange(type="text", subtype="plain", quality=0.5),
            http.MediaRange(type="text", subtype="plain", quality=0.8),
        )

    def test_lt_ranged_subtype(self):
        self.assertLess(
            http.MediaRange(type="text"),
            http.MediaRange(type="text", subtype="plain"),
        )

    def test_lt_ranged_type_and_subtype(self):
        self.assertLess(http.MediaRange(), http.MediaRange(type="text"))

    def test_lt_ranged_lower_quality(self):
        self.assertLess(
            http.MediaRange(type="text", quality=0.3),
            http.MediaRange(quality=0.5),
        )

    def test_lt_different_type_and_subtype(self):
        self.assertLess(
            http.MediaRange(type="application", subtype="json", quality=0.5),
            http.MediaRange(type="text", subtype="plain", quality=0.8),
        )

    def test_lt_parameters_same_type_and_subtype(self):
        self.assertLess(
            http.MediaRange(type="bar", subtype="foo"),
            http.MediaRange(type="bar", subtype="foo", parameters={"a": "b"}),
        )

    def test_not_lt_same_type_and_subtype(self):
        self.assertFalse(
            http.MediaRange(type="text", subtype="plain", quality=0.8) <
            http.MediaRange(type="text", subtype="plain", quality=0.5),
        )

    def test_not_lt_different_type_and_subtype(self):
        self.assertFalse(
            http.MediaRange(type="application", subtype="json") <
            http.MediaRange(type="text", subtype="plain"),
        )

    def test_not_lt_parameters(self):
        self.assertFalse(
            http.MediaRange(type="bar", subtype="foo", parameters={"a": "b"}) <
            http.MediaRange(type="bar", subtype="foo"),
        )

    def test_not_lt_parameters_different_type(self):
        self.assertFalse(
            http.MediaRange(type="foo", subtype="foo") <
            http.MediaRange(type="bar", subtype="foo", parameters={"a": "b"}),
        )

    def test_not_lt_parameters_different_subtype(self):
        self.assertFalse(
            http.MediaRange(type="bar", subtype="foo") <
            http.MediaRange(type="bar", subtype="baz", parameters={"a": "b"}),
        )

    def test_not_lt_ranged_subtype(self):
        self.assertFalse(
            http.MediaRange(type="text", subtype="plain") <
            http.MediaRange(type="text"),
        )

    def test_not_lt_ranged_lower_quality(self):
        self.assertFalse(
            http.MediaRange(quality=0.5) <
            http.MediaRange(type="text", quality=0.3),
        )

    def test_lt_equal_range(self):
        self.assertFalse(http.MediaRange() < http.MediaRange())

    def test_hash(self):
        self.assertEqual(
            {
                http.MediaRange(type="text", subtype="plain", quality=0.8),
                http.MediaRange(type="text", subtype="plain", quality=0.8),
            },
            {http.MediaRange(type="text", subtype="plain", quality=0.8)},
        )

    def test_hash_parameters(self):
        self.assertEqual(
            {
                http.MediaRange(type="a", parameters={"a": "b"}),
                http.MediaRange(type="a", parameters={"a": "b"}),
            },
            {http.MediaRange(type="a", parameters={"a": "b"})},
        )

    def test_hash_different_parameters(self):
        self.assertNotEqual(
            hash(http.MediaRange(type="a", parameters={"a": "b"})),
            hash(http.MediaRange(type="a", parameters={"a": "c"})),
        ),
