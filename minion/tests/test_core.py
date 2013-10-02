from unittest import TestCase, skipIf
import mock

try:
    import jinja2
except ImportError:
    jinja2 = None

from minion import core, resource
from minion.compat import iteritems, viewitems
from minion.request import Request
from minion.routers import SimpleRouter


class TestApplication(TestCase):
    def test_it_delegates_routes_to_the_router(self):
        router = mock.Mock(spec=SimpleRouter())
        application = core.Application(router=router)

        fn = mock.Mock()
        application.route("/foo/bar", baz=2)(fn)

        router.add_route.assert_called_once_with("/foo/bar", fn, baz=2)

    def test_binds_to_its_bin(self):
        app = core.Application()
        expected = {"app" : app, "config" : app.config}
        self.assertEqual(
            {k : v for k, v in iteritems(app.bin.globals) if k in expected},
            expected,
        )

    def test_it_can_bind_to_other_bins(self):
        app = core.Application()
        bin = resource.Bin()
        app.bind_bin(bin)
        expected = {"app" : app, "config" : app.config}
        self.assertEqual(
            {k : v for k, v in iteritems(bin.globals) if k in expected},
            expected,
        )

    @skipIf(jinja2 is None, "jinja2 not found")
    def test_it_can_bind_to_jinja_environments(self):
        environment = jinja2.Environment()
        application = core.Application(jinja=environment)
        self.assertEqual(application.bin.globals["jinja"], environment)
        self.assertGreaterEqual(
            viewitems(environment.globals), {
                ("app", application),
                ("router", application.router),
            },
        )


class TestApplicationIntegration(TestCase):
    def setUp(self):
        self.router = mock.Mock(spec=SimpleRouter())
        self.application = core.Application(router=self.router)

    def test_it_serves_matched_requests(self):
        view, _ = self.router.match.return_value = mock.Mock(), {"foo" : 12}
        request = mock.Mock(spec=Request(path="/"))
        self.application.serve(request)
        view.assert_called_once_with(request, foo=12)

    def test_it_serves_404s_for_unmatched_requests_by_default(self):
        view, _ = self.router.match.return_value = None, {}
        request = mock.Mock(spec=Request(path="/"))
        response = self.application.serve(request)
        self.assertEqual(response.code, 404)
