from unittest import TestCase, skipIf
import json

from future.utils import PY3

from minion import routing
from minion.http import URL
from minion.request import Request, Response, redirect
from minion.traversal import LeafResource


class ReverseRenderer(object):
    def render(self, request, response):
        return Response(b"".join(reversed(response.content)))


def view(request, **kwargs):
    return Response(json.dumps(kwargs))


class TestRouter(TestCase):
    def setUp(self):
        self.router = routing.Router(mapper=routing.SimpleMapper())

    def test_route(self):
        self.router.add(b"/", view)
        request = Request(url=URL(path=b"/"))
        response = self.router.route(request, path=b"/")
        self.assertEqual(response, view(request))

    def test_unknown_route(self):
        request = Request(url=URL(path=b"/404"))
        response = self.router.route(request, path=b"/404")
        self.assertEqual(response, Response(code=404))

    def test_specified_renderer(self):
        self.router.add(b"/", view, renderer=ReverseRenderer())
        request = Request(url=URL(path=b"/"))
        response = self.router.route(request, path=b"/")
        self.assertEqual(response, Response(b"}{"))

    def test_specified_renderer_multiple_routes(self):
        self.router.add(b"/", view, methods=[b"GET"], renderer=None)
        self.router.add(
            b"/", view, methods=[b"POST"], renderer=ReverseRenderer(),
        )

        get = Request(url=URL(path=b"/"), method=b"GET")
        response = self.router.route(get, path=b"/")
        self.assertEqual(response, Response(b"{}"))

        post = Request(url=URL(path=b"/"), method=b"POST")
        response = self.router.route(post, path=b"/")
        self.assertEqual(response, Response(b"}{"))

    def test_renderer_with_render_error_handler(self):
        class RendererWithErrorHandler(object):
            def render(self, request, response):
                raise ZeroDivisionError()

            def render_error(self, request, response, exc):
                return Response(response.content + exc.__class__.__name__)

        self.router.add(b"/", view, renderer=RendererWithErrorHandler())
        response = self.router.route(Request(url=URL(path=b"/")), path=b"/")
        self.assertEqual(response, Response(b"{}ZeroDivisionError"))

    def test_renderer_without_error_handler(self):
        class RendererWithoutErrorHandler(object):
            def render(self, request, response):
                raise ZeroDivisionError()

        self.router.add(b"/", view, renderer=RendererWithoutErrorHandler())
        request = Request(url=URL(path=b"/"))

        with self.assertRaises(ZeroDivisionError):
            self.router.route(request, path=b"/")

    def test_renderer_with_view_error_handler(self):
        class RendererWithErrorHandler(object):
            def render(self, request, response):
                raise ZeroDivisionError("I won't ever get raised")

            def view_error(self, request, error):
                return Response(error.__class__.__name__)

        def boom(request):
            raise IndexError()

        self.router.add(b"/", boom, renderer=RendererWithErrorHandler())
        response = self.router.route(Request(url=URL(path=b"/")), path=b"/")
        self.assertEqual(response, Response(b"IndexError"))


class TestRouterDefaultRenderer(TestCase):
    def setUp(self):
        self.router = routing.Router(
            mapper=routing.SimpleMapper(), default_renderer=ReverseRenderer(),
        )

    def test_default_renderer(self):
        self.router.add(b"/", view)
        request = Request(url=URL(path=b"/"))
        response = self.router.route(request, path=b"/")
        self.assertEqual(response, Response(b"}{"))

    def test_disable_default_renderer(self):
        self.router.add(b"/", view, renderer=None)
        request = Request(url=URL(path=b"/"))
        response = self.router.route(request, path=b"/")
        self.assertEqual(response, Response(b"{}"))


class MapperTestMixin(object):
    """
    Test basic functionality common to all mappers.

    Expects a mapper to be present and instantiated at the `mapper` attribute
    of the test case.

    """

    def test_it_maps_routes(self):
        self.mapper.add(b"/route", view)
        render = self.mapper.map(
            Request(url=URL(path=b"/route")), path=b"/route",
        )
        self.assertIs(render, view)

    def test_it_maps_routes_for_specified_methods(self):
        self.mapper.add(b"/route", view, methods=[b"POST"])
        request = Request(url=URL(path=b"/route"), method=b"POST")
        self.assertEqual(self.mapper.map(request, path=b"/route"), view)

    def test_it_does_not_map_routes_for_unspecified_methods(self):
        self.mapper.add(b"/route", view, methods=[b"POST"])
        request = Request(url=URL(path=b"/route"), method=b"GET")
        self.assertIsNone(self.mapper.map(request, path=b"/route"))

    def test_it_maps_multiple_routes_for_specified_methods(self):
        self.mapper.add(b"/", lambda r : Response(b"GET"), methods=[b"GET"])
        self.mapper.add(b"/", lambda r : Response(b"POST"), methods=[b"POST"])

        get = Request(url=URL(path=b"/"), method=b"GET")
        post = Request(url=URL(path=b"/"), method=b"POST")
        map = self.mapper.map
        self.assertEqual(
            (map(get, path=b"/")(get), map(post, path=b"/")(post)),
            (Response(b"GET"), Response(b"POST")),
        )

    def test_it_can_build_named_routes(self):
        self.mapper.add(b"/", view, route_name=u"home")
        self.assertEqual(self.mapper.lookup(u"home"), b"/")

    def test_unknown_route_names_become_literal_paths(self):
        self.assertEqual(self.mapper.lookup(b"/work"), b"/work")

    def test_it_does_not_map_unknown_paths(self):
        request = Request(url=URL(path=b"/route"))
        render = self.mapper.map(request, path=b"/route")
        self.assertIsNone(render)

    def test_extra_build_arguments_become_query_strings(self):
        self.mapper.add(b"/", view, route_name=u"home")
        url = self.mapper.lookup(u"home", thing=b"yes")
        self.assertEqual(url, b"/?thing=yes")


class TestTraversalMapper(TestCase):
    def test_it_traverses_children(self):
        class Resource(object):
            def get_child(self, name, request):
                return LeafResource(
                    render=lambda request : Response(b"Hello " + name),
                )

        mapper = routing.TraversalMapper(root=Resource())
        request = Request(url=URL(path=b"/world"))
        render = mapper.map(request, path=b"/world")
        self.assertEqual(render(request), Response(content=b"Hello world"))


class TestTraversalMapperStatic(MapperTestMixin, TestCase):
    def setUp(self):
        self.mapper = routing.TraversalMapper(root=LeafResource(render=None))


@skipIf(not hasattr(routing, "RoutesMapper"), "Routes not found")
@skipIf(PY3, "WSGI on Py3 is insanity")
class TestRoutesMapper(MapperTestMixin, TestCase):
    def setUp(self):
        self.mapper = routing.RoutesMapper()

    def test_it_maps_routes_with_arguments(self):
        self.mapper.add(b"/route/{year}", view, stuff=b"12")
        request = Request(url=URL(path=b"/route/2013"))
        render = self.mapper.map(request, path=b"/route/2013")
        self.assertEqual(
            json.loads(render(request).content),
            {b"year" : b"2013", b"stuff" : b"12"},
        )

    def test_it_builds_routes_with_arguments(self):
        self.mapper.add(b"/{year}", view, route_name=u"year")
        url = self.mapper.lookup(b"year", year=2012)
        self.assertEqual(url, b"/2012")


@skipIf(not hasattr(routing, "WerkzeugMapper"), "Werkzeug not found")
@skipIf(PY3, "WSGI on Py3 is insanity")
class TestWerkzeugMapper(MapperTestMixin, TestCase):
    def setUp(self):
        self.mapper = routing.WerkzeugMapper()

    def test_it_maps_routes_with_arguments(self):
        self.mapper.add(b"/route/<int:year>", view)
        request = Request(url=URL(path=b"/route/2013"))
        render = self.mapper.map(request, path=b"/route/2013")
        self.assertEqual(json.loads(render(request).content), {b"year" : 2013})

    def test_it_builds_routes_with_arguments(self):
        self.mapper.add(b"/<int:year>", view, route_name=u"year")
        url = self.mapper.lookup(u"year", year=2012)
        self.assertEqual(url, b"/2012")

    def test_it_handles_routing_redirects(self):
        self.mapper.add(b"/<int:year>/", view)
        request = Request(url=URL(path=b"/2013"))
        render = self.mapper.map(request, path=b"/2013")
        self.assertEqual(
            render(request), redirect(b"http:///2013/", code=301),
        )


class TestSimpleMapper(MapperTestMixin, TestCase):
    def setUp(self):
        self.mapper = routing.SimpleMapper()
