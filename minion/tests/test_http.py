from unittest import TestCase

from minion import http


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
        self.assertEqual(
            repr(headers),
            "<" + self.Headers.__name__ + " Foo=['bar'] Thing=['baz', 'quux']>"
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

        second.add_value(b"foo", "bar")
        self.assertEqual(first, second)

        second.add_value(b"foo", "baz")
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
