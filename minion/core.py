from collections import defaultdict

import attr

from minion import assets
from minion.request import Manager
from minion.routing import Router, SimpleMapper


@attr.s
class Application(object):
    """
    A Minion application.

    Arguments:

        config (collections.MutableMapping):

            any app configuration

        bin (assets.Bin):

            an asset bin containing assets used by views.

            If unprovided, an empty one will be created (until it is
            populated).

        manager (request.Manager):

            a request manager, which managers state during each request.

            If unprovided, one will be created and used.

        router:

            an object satisfying the router interface (see `minion.routing`) to
            use for route addition and generation for this application.

            If unprovided, a router with simple dictionary lookup will be used.

        jinja (jinja2.Environment):

            a pre-configured jinja2 environment, if using jinja2 is desired.

            (One can be added later, or multiple environments used, by calling
            `bind_jinja_environment`.)

    """

    config = attr.ib(default=attr.Factory(dict))
    manager = attr.ib(default=attr.Factory(Manager), repr=False)
    bin = attr.ib(default=None, repr=False)
    router = attr.ib(
        default=attr.Factory(lambda: Router(mapper=SimpleMapper())),
    )
    _jinja = attr.ib(default=None)

    def __attrs_post_init__(self):
        if self.bin is None:
            self.bin = assets.Bin(manager=self.manager)
        self.bin = self.bound_bin(self.bin)
        if self._jinja is not None:
            self.bind_jinja_environment(self._jinja)

    def route(self, route, **kwargs):
        def _add_route(fn):
            self.router.add(route, fn, **kwargs)
            return fn
        return _add_route

    def serve(self, request, path):
        self.manager.request_started(request)
        response = self.router.route(request=request, path=path)
        self.manager.request_served(request, response)
        return response

    def bound_bin(self, bin):
        """
        Bind an asset bin to this application.

        Returns:

            Bin: a bin containing this application's relevant globals

        """

        return bin.with_globals(
            app=self,
            config=self.config,
            manager=self.manager,
            router=self.router,
        )

    def bind_jinja_environment(self, environment, asset_name="jinja"):
        """
        Bind useful pieces of the application to the given Jinja2 environment.

        Arguments:

            environment (jinja2.Environment):

                the environment to bind

            asset_name (str):

                a name to bind to in the application's asset bin.

                The default is ``'jinja'``.

        """

        environment.globals.update(
            [
                ("app", self),
                ("config", self.config),
                ("router", self.router),
            ],
        )
        self.bin = self.bin.with_globals(**{asset_name: environment})
