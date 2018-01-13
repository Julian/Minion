from unittest import TestCase, skipIf

from future.utils import iteritems
from hyperlink import URL

try:
    import jinja2
except ImportError:
    jinja2 = None

from minion import core, assets
from minion.request import Manager, Request, Response
from minion.routing import Router, SimpleMapper


class TestApplication(TestCase):
    def assertSubdict(self, subdict, of):
        """
        Assert that the given thing is a subdict of the given dict.

        """

        subdict = dict(subdict)
        matches = {k: v for k, v in iteritems(of) if k in subdict}
        self.assertEqual(subdict, matches)

    def test_it_delegates_routes_to_the_router(self):
        class Router(object):
            def add(this, route, fn, baz):
                self.added = route, fn, baz

        application = core.Application(router=Router())

        @application.route("/foo", baz=2)
        def fn(request):
            pass

        self.assertEqual(getattr(self, "added", None), ("/foo", fn, 2))

    def test_binds_to_its_bin(self):
        app = core.Application()
        self.assertEqual(
            (
                app.bin.provide("app"),
                app.bin.provide("config"),
                app.bin.provide("manager"),
                app.bin.provide("router"),
            ), (
                app,
                app.config,
                app.manager,
                app.router,
            ),
        )

    def test_it_can_bind_to_other_bins(self):
        app = core.Application()
        bin = app.bound_bin(assets.Bin())
        self.assertEqual(
            (
                bin.provide("app"),
                bin.provide("config"),
                bin.provide("manager"),
                bin.provide("router"),
            ), (
                app,
                app.config,
                app.manager,
                app.router,
            ),
        )

    @skipIf(jinja2 is None, "jinja2 not found")
    def test_it_can_bind_to_jinja_environments(self):
        environment = jinja2.Environment()
        app = core.Application(jinja=environment)
        self.assertEqual(app.bin.provide("jinja"), environment)


class TestApplicationIntegration(TestCase):
    def setUp(self):
        self.manager = Manager()
        self.router = Router(mapper=SimpleMapper())
        self.app = core.Application(manager=self.manager, router=self.router)
        self.request = Request(url=URL(path=[u""]))

    def test_it_serves_mapped_requests(self):
        self.router.add(
            self.request.url.path, lambda request: Response(b"Hello"),
        )
        self.assertEqual(
            self.app.serve(self.request, path=self.request.url.path),
            Response(b"Hello"),
        )

    def test_it_serves_404s_for_unmapped_requests_by_default(self):
        self.assertEqual(
            self.app.serve(self.request, path=self.request.url.path).code, 404,
        )
