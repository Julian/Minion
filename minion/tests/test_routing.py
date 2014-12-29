from unittest import TestCase, skipIf

from future.utils import PY3

from minion import routing
from minion.http import URL
from minion.request import Request, Response, redirect
from minion.traversal import LeafResource


class ReverseRenderer(object):
    def render(self, request, response):
        return Response(b"".join(reversed(response.content)))


def view(request):
    return Response(b"Is anybody out there?")


class TestRouter(TestCase):
    def setUp(self):
        self.router = routing.Router(mapper=routing.SimpleMapper())

    def test_route(self):
        self.router.add(b"/", view)
        request = Request(url=URL(path=b"/"))
        response = self.router.route(request)
        self.assertEqual(response, view(request))

    def test_unknown_route(self):
        request = Request(url=URL(path=b"/404"))
        response = self.router.route(request)
        self.assertEqual(response, Response(code=404))

    def test_specified_renderer(self):
        self.router.add(b"/", view, renderer=ReverseRenderer())
        request = Request(url=URL(path=b"/"))
        response = self.router.route(request)
        self.assertEqual(response, Response(b"?ereht tuo ydobyna sI"))

    def test_specified_renderer_multiple_routes(self):
        self.router.add(b"/", view, methods=[b"GET"], renderer=None)
        self.router.add(
            b"/", view, methods=[b"POST"], renderer=ReverseRenderer(),
        )

        get = Request(url=URL(path=b"/"), method=b"GET")
        response = self.router.route(get)
        self.assertEqual(response, Response(b"Is anybody out there?"))

        post = Request(url=URL(path=b"/"), method=b"POST")
        response = self.router.route(post)
        self.assertEqual(response, Response(b"?ereht tuo ydobyna sI"))

    def test_renderer_with_render_error_handler(self):
        class RendererWithErrorHandler(object):
            def render(self, request, response):
                raise ZeroDivisionError()

            def render_error(self, request, response, exc):
                return Response(response.content[:2] + exc.__class__.__name__)

        self.router.add(b"/", view, renderer=RendererWithErrorHandler())
        response = self.router.route(Request(url=URL(path=b"/")))
        self.assertEqual(response, Response(b"IsZeroDivisionError"))

    def test_renderer_without_error_handler(self):
        class RendererWithoutErrorHandler(object):
            def render(self, request, response):
                raise ZeroDivisionError()

        self.router.add(b"/", view, renderer=RendererWithoutErrorHandler())
        request = Request(url=URL(path=b"/"))

        with self.assertRaises(ZeroDivisionError):
            self.router.route(request)

    def test_renderer_with_view_error_handler(self):
        class RendererWithErrorHandler(object):
            def render(self, request, response):
                raise ZeroDivisionError("I won't ever get raised")

            def view_error(self, request, error):
                return Response(error.__class__.__name__)

        def boom(request):
            raise IndexError()

        self.router.add(b"/", boom, renderer=RendererWithErrorHandler())
        response = self.router.route(Request(url=URL(path=b"/")))
        self.assertEqual(response, Response(b"IndexError"))


class MapperTestMixin(object):
    """
    Test basic functionality common to all mappers.

    Expects a mapper to be present and instantiated at the `mapper` attribute
    of the test case.

    """

    def test_it_maps_routes(self):
        self.mapper.add(b"/route", view)
        mapped = self.mapper.map(Request(url=URL(path=b"/route")))
        self.assertEqual(mapped, (view, {}))

    def test_it_maps_routes_for_specified_methods(self):
        self.mapper.add(b"/route", view, methods=[b"POST"])
        request = Request(url=URL(path=b"/route"), method=b"POST")
        self.assertEqual(self.mapper.map(request), (view, {}))

    def test_it_does_not_map_routes_for_unspecified_methods(self):
        self.mapper.add(b"/route", view, methods=[b"POST"])
        request = Request(url=URL(path=b"/route"), method=b"GET")
        self.assertEqual(self.mapper.map(request), (None, {}))

    def test_it_maps_multiple_routes_for_specified_methods(self):
        self.mapper.add(b"/", lambda r : Response(b"GET"), methods=[b"GET"])
        self.mapper.add(b"/", lambda r : Response(b"POST"), methods=[b"POST"])

        get = Request(url=URL(path=b"/"), method=b"GET")
        post = Request(url=URL(path=b"/"), method=b"POST")
        self.assertEqual(
            (self.mapper.map(get)[0](get), self.mapper.map(post)[0](post)),
            (Response(b"GET"), Response(b"POST")),
        )

    def test_it_can_build_named_routes(self):
        self.mapper.add(b"/", view, route_name=u"home")
        self.assertEqual(self.mapper.lookup(u"home"), b"/")

    def test_unknown_route_names_become_literal_paths(self):
        self.assertEqual(self.mapper.lookup(b"/work"), b"/work")

    def test_it_does_not_map_unknown_paths(self):
        mapped = self.mapper.map(Request(url=URL(path=b"/route")))
        self.assertEqual(mapped, (None, {}))

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
        mapped, kwargs = mapper.map(request)
        self.assertEqual(mapped(request), Response(content=b"Hello world"))


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
        mapped = self.mapper.map(Request(url=URL(path=b"/route/2013")))
        self.assertEqual(
            mapped, (view, {b"year" : b"2013", b"stuff" : b"12"}),
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
        mapped = self.mapper.map(Request(url=URL(path=b"/route/2013")))
        self.assertEqual(mapped, (view, {b"year" : 2013}))

    def test_it_builds_routes_with_arguments(self):
        self.mapper.add(b"/<int:year>", view, route_name=u"year")
        url = self.mapper.lookup(u"year", year=2012)
        self.assertEqual(url, b"/2012")

    def test_it_handles_routing_redirects(self):
        self.mapper.add(b"/<int:year>/", view)
        request = Request(url=URL(path=b"/2013"))
        mapped, _ = self.mapper.map(request)
        self.assertEqual(
            mapped(request), redirect(b"http:///2013/", code=301),
        )


class TestSimpleMapper(MapperTestMixin, TestCase):
    def setUp(self):
        self.mapper = routing.SimpleMapper()
