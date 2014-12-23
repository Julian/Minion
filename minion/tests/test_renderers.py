# -*- coding: utf-8 -*-
from unittest import TestCase

from minion import Response, renderers


class TestUnicodeRenderer(TestCase):
    def test_it_renders_via_the_given_encoding(self):
        renderer = renderers.Unicode(encoding="utf-8")
        self.assertEqual(renderer.render(u"שלום"), Response(b"שלום"))

    def test_encoding_ignoring_errors(self):
        renderer = renderers.Unicode(encoding="ascii", errors="ignore")
        self.assertEqual(renderer.render(u"שלום"), Response(b""))

    def test_encoding_errors_by_default(self):
        renderer = renderers.Unicode(encoding="ascii")
        with self.assertRaises(UnicodeEncodeError):
            self.assertEqual(renderer.render(u"שלום"))

    def test_UTF8(self):
        response = renderers.UTF8.render(u"שלום")
        self.assertEqual(response, Response(b"שלום"))
