# -*- coding: utf-8 -*-
from collections import OrderedDict
from unittest import TestCase
import json

from hyperlink import URL

from minion import renderers
from minion.http import Headers
from minion.request import Request, Response


class TestUnicodeRenderer(TestCase):

    request = Request(url=URL(path=[u""]))

    def test_it_renders_via_the_given_encoding(self):
        renderer = renderers.Unicode(encoding="utf-8")
        render = renderers.bind(renderer, to=lambda _: u"שלום")
        self.assertEqual(
            render(self.request), Response(u"שלום".encode("utf-8")),
        )

    def test_encoding_ignoring_errors(self):
        renderer = renderers.Unicode(encoding="ascii", errors="ignore")
        render = renderers.bind(renderer, to=lambda _: u"שלום")
        self.assertEqual(render(self.request), Response(b""))

    def test_encoding_errors_by_default(self):
        renderer = renderers.Unicode(encoding="ascii")
        render = renderers.bind(renderer, to=lambda _: u"שלום")
        with self.assertRaises(UnicodeEncodeError):
            render(self.request)

    def test_UTF8(self):
        render = renderers.bind(renderers.UTF8, to=lambda _: u"שלום")
        self.assertEqual(
            render(self.request), Response(u"שלום".encode("utf-8")),
        )


class TestJSON(TestCase):
    def assertPretty(self, content, response):
        self.assertNotEqual(
            response, Response(
                headers=Headers([("Content-Type", ["application/json"])]),
                content=json.dumps(content),
            ),
        )
        self.assertEqual(
            response, Response(
                headers=Headers([("Content-Type", ["application/json"])]),
                content=json.dumps(content, indent=2, sort_keys=True)
            ),
        )

    def assertNotPretty(self, content, response):
        self.assertEqual(
            response, Response(
                headers=Headers([("Content-Type", ["application/json"])]),
                content=json.dumps(content, separators=",:"),
            ),
        )
        self.assertNotEqual(
            response, Response(
                headers=Headers([("Content-Type", ["application/json"])]),
                content=json.dumps(content, indent=2, sort_keys=True)
            ),
        )

    def test_it_dumps_pretty_json_for_humans(self):
        content = ["a", "b", "c"]
        render = renderers.bind(renderers.JSON(), to=lambda _: content)
        request = Request(
            url=URL(path=[u""]),
            headers=Headers([("Accept", ["*/*"])]),
        )
        self.assertPretty(content, render(request))

    def test_it_dumps_pretty_json_for_humans_no_accept_header(self):
        content = ["a", "b", "c"]
        render = renderers.bind(renderers.JSON(), to=lambda _: content)
        self.assertPretty(content, render(Request(url=URL(path=[u""]))))

    def test_it_dumps_practical_json_for_machines(self):
        content = ["a", "b", "c"]
        render = renderers.bind(renderers.JSON(), to=lambda _: content)
        request = Request(
            url=URL(path=[u""]),
            headers=Headers([("Accept", ["application/json"])]),
        )
        self.assertNotPretty(content, render(request))

    def test_dict_sort_keys(self):
        content = OrderedDict([("foo", "bar"), ("baz", "quux")])
        render = renderers.bind(renderers.JSON(), to=lambda _: content)
        request = Request(
            url=URL(path=[u""]),
            headers=Headers([("Accept", ["*/*"])]),
        )
        self.assertPretty(content, render(request))

    def test_separators(self):
        render = renderers.bind(renderers.JSON(), to=lambda _: dict(a=1, b=2))
        request = Request(
            url=URL(path=[u""]),
            headers=Headers([("Accept", ["application/json"])]),
        )
        response = render(request)
        self.assertEqual(
            response, Response(
                content=response.content,
                headers=Headers([("Content-Type", ["application/json"])]),
            ),
        )
        self.assertNotIn(response.content, " ")
        self.assertEqual(json.loads(response.content), {"a": 1, "b": 2})

    def test_customized_dumps(self):
        """
        A customized dumps applies to both pretty and non-pretty responses.

        """

        renderer = renderers.JSON(default=lambda obj: 23)
        render = renderers.bind(renderer, to=lambda _: {"foo": object()})
        request = Request(
            url=URL(path=[u""]),
            headers=Headers([("Accept", ["application/json"])]),
        )
        self.assertEqual(
            render(request), Response(
                content=b'{"foo":23}',
                headers=Headers([("Content-Type", ["application/json"])]),
            ),
        )
        self.assertEqual(
            render(Request(url=URL(path=[u""]))), Response(
                content=b'{\n  "foo": 23\n}',
                headers=Headers([("Content-Type", ["application/json"])]),
            ),
        )


class TestSimpleJSON(TestCase):

    request = Request(url=URL(path=[u""]))

    def test_it_dumps_json(self):
        renderer = renderers.SimpleJSON()
        render = renderers.bind(renderer, to=lambda _: {"foo": "bar"})
        self.assertEqual(render(self.request), Response(b'{"foo": "bar"}'))

    def test_customized_dumps(self):
        renderer = renderers.SimpleJSON(separators=",:")
        render = renderers.bind(renderer, to=lambda _: {"foo": "bar"})
        self.assertEqual(render(self.request), Response(b'{"foo":"bar"}'))
