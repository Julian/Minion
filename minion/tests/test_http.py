from unittest import TestCase

from minion import http
from minion.compat import PY3


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
            fields = " b'Foo'=[b'bar'] b'Thing'=[b'baz', b'quux']>"
        else:
            fields = " Foo=['bar'] Thing=['baz', 'quux']>"

        self.assertEqual(repr(headers), "<" + self.Headers.__name__ + fields)


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
