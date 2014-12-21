from unittest import TestCase, skipIf
import mock

try:
    import jinja2
except ImportError:
    jinja2 = None

from minion import core, assets
from minion.compat import iteritems
from minion.request import Manager, Request, Response
from minion.routing import Router, SimpleMapper


class TestApplication(TestCase):
    def assertSubdict(self, subdict, of):
        """
        Assert that the given thing is a subdict of the given dict.

        """

        subdict = dict(subdict)
        matches = {k : v for k, v in iteritems(of) if k in subdict}
        self.assertEqual(subdict, matches)

    def test_it_delegates_routes_to_the_router(self):
        router = mock.Mock(spec=SimpleMapper())
        application = core.Application(router=router)

        fn = mock.Mock()
        application.route("/foo/bar", baz=2)(fn)

        router.add.assert_called_once_with("/foo/bar", fn, baz=2)

    def test_binds_to_its_bin(self):
        app = core.Application()
        self.assertSubdict(
            [
                ("app", app),
                ("config", app.config),
                ("manager", app.manager),
                ("router", app.router),
            ],
            app.bin.globals,
        )

    def test_it_can_bind_to_other_bins(self):
        app = core.Application()
        bin = assets.Bin(manager=app.manager)
        app.bind_bin(bin)
        self.assertSubdict(
            [
                ("app", app),
                ("config", app.config),
                ("manager", app.manager),
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
        self.manager = mock.Mock(spec=Manager())
        self.router = Router(mapper=SimpleMapper())
        self.app = core.Application(manager=self.manager, router=self.router)
        self.request = Request(path="/")

    def test_it_starts_and_stops_the_request(self):
        self.router.add(self.request.path, lambda request : Response(b"Hello"))
        self.app.serve(self.request)
        self.assertEqual(
            self.manager.mock_calls, [
                mock.call.request_started(self.request),
                mock.call.request_served(self.request, Response(b"Hello")),
            ],
        )

    def test_it_serves_mapped_requests(self):
        self.router.add(self.request.path, lambda request : Response(b"Hello"))
        self.assertEqual(self.app.serve(self.request), Response(b"Hello"))

    def test_it_serves_404s_for_unmapped_requests_by_default(self):
        self.assertEqual(self.app.serve(self.request).code, 404)
