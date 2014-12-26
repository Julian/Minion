# -*- coding: utf-8 -*-
from unittest import TestCase
import json

from minion import Response, renderers
from minion.http import Accept
from minion.request import Request


class TestUnicodeRenderer(TestCase):

    request = Request(path=b"/")

    def test_it_renders_via_the_given_encoding(self):
        renderer = renderers.Unicode(encoding="utf-8")
        render = renderers.bind(renderer, to=lambda _ : u"שלום")
        self.assertEqual(render(self.request), Response(b"שלום"))

    def test_encoding_ignoring_errors(self):
        renderer = renderers.Unicode(encoding="ascii", errors="ignore")
        render = renderers.bind(renderer, to=lambda _ : u"שלום")
        self.assertEqual(render(self.request), Response(b""))

    def test_encoding_errors_by_default(self):
        renderer = renderers.Unicode(encoding="ascii")
        render = renderers.bind(renderer, to=lambda _ : u"שלום")
        with self.assertRaises(UnicodeEncodeError):
            render(self.request)

    def test_UTF8(self):
        render = renderers.bind(renderers.UTF8, to=lambda _ : u"שלום")
        self.assertEqual(render(self.request), Response(b"שלום"))


class TestJSON(TestCase):
    def test_it_dumps_pretty_json_for_humans(self):
        pass


class TestSimpleJSON(TestCase):

    request = Request(path=b"/")

    def test_it_dumps_json(self):
        renderer = renderers.SimpleJSON()
        render = renderers.bind(renderer, to=lambda _ : {"foo" : "bar"})
        self.assertEqual(render(self.request), Response(b'{"foo": "bar"}'))

    def test_customized_dumps(self):
        renderer = renderers.SimpleJSON(separators=",:")
        render = renderers.bind(renderer, to=lambda _ : {"foo" : "bar"})
        self.assertEqual(render(self.request), Response(b'{"foo":"bar"}'))
