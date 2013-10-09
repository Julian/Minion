from unittest import TestCase, skipIf
import mock

try:
    import jinja2
except ImportError:
    jinja2 = None

from minion import core, resource
from minion.compat import iteritems
from minion.request import Request, Response
from minion.routers import SimpleRouter


class TestApplication(TestCase):
    def assertSubdict(self, subdict, of):
        """
        Assert that the given thing is a subdict of the given dict.

        """

        subdict = dict(subdict)
        matches = {k : v for k, v in iteritems(of) if k in subdict}
        self.assertEqual(subdict, matches)

    def test_it_delegates_routes_to_the_router(self):
        router = mock.Mock(spec=SimpleRouter())
        application = core.Application(router=router)

        fn = mock.Mock()
        application.route("/foo/bar", baz=2)(fn)

        router.add_route.assert_called_once_with("/foo/bar", fn, baz=2)

    def test_binds_to_its_bin(self):
        app = core.Application()
        self.assertSubdict(
            [
                ("app", app),
                ("config", app.config),
                ("router", app.router),
            ],
            app.bin.globals,
        )

    def test_it_can_bind_to_other_bins(self):
        app = core.Application()
        bin = resource.Bin()
        app.bind_bin(bin)
        self.assertSubdict(
            [
                ("app", app),
                ("config", app.config),
                ("router", app.router),
            ],
            bin.globals,
        )

    @skipIf(jinja2 is None, "jinja2 not found")
    def test_it_can_bind_to_jinja_environments(self):
        environment = jinja2.Environment()
        app = core.Application(jinja=environment)
        self.assertEqual(app.bin.globals["jinja"], environment)
        self.assertSubdict(
            [
                ("app", app),
                ("config", app.config),
                ("router", app.router),
            ],
            environment.globals,
        )


class TestApplicationIntegration(TestCase):
    def setUp(self):
        self.router = mock.Mock(spec=SimpleRouter())
        self.application = core.Application(router=self.router)
        self.request = mock.Mock(spec=Request(path="/"))

    def test_it_serves_matched_requests(self):
        view, _ = self.router.match.return_value = mock.Mock(), {"foo" : 12}
        self.application.serve(self.request)
        view.assert_called_once_with(self.request, foo=12)

    def test_it_serves_404s_for_unmatched_requests_by_default(self):
        view, _ = self.router.match.return_value = None, {}
        response = self.application.serve(self.request)
        self.assertEqual(response.code, 404)

    def test_after_response(self):
        thing = mock.Mock(return_value=None)
        self.application.after_response(self.request, thing, 1, kw="abc")

        view, _ = self.router.match.return_value = None, {}
        response = self.application.serve(self.request)

        thing.assert_called_once_with(self.request, response, 1, kw="abc")

    def test_after_response_can_modify_the_response(self):
        def double_text(request, response):
            return Response(response.content * 2)

        self.application.after_response(self.request, double_text)

        view = mock.Mock(return_value=Response("Hello"))
        self.router.match.return_value = view, {}

        response = self.application.serve(self.request)

        self.assertEqual(response.content, "HelloHello")

    def test_after_response_chaining(self):
        def double_text(request, response):
            return Response(response.content * 2)

        def world(request, response):
            return Response(response.content + "World")

        self.application.after_response(self.request, double_text)
        self.application.after_response(self.request, world)

        view = mock.Mock(return_value=Response("Hello"))
        self.router.match.return_value = view, {}

        response = self.application.serve(self.request)

        self.assertEqual(response.content, "HelloHelloWorld")
