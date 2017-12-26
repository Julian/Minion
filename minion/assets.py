from functools import wraps

from pyrsistent import m, pset
import attr


class DuplicateAsset(Exception):
    pass


class NoSuchAsset(LookupError):
    pass


@attr.s
class Bin(object):

    _manager = attr.ib()
    _globals = attr.ib(default=m())

    _assets = attr.ib(default=m())
    _needs_request = attr.ib(default=pset())

    def __contains__(self, asset):
        return asset in self._assets or asset in self._globals

    @property
    def assets(self):
        return pset(self._assets).update(self._globals)

    def provides(self, asset, needs_request=False):
        """
        Declare that the decorated callable provides the given asset.

        Arguments:

            asset (str):

                the name of the new asset

            needs_request (bool):

                whether to pass the request in to the given callable when
                calling it
        """

        def _provides(fn):
            if asset in self:
                raise DuplicateAsset(asset)
            self._assets = self._assets.set(asset, fn)

            if needs_request:
                self._needs_request = self._needs_request.add(asset)

            return fn
        return _provides

    def with_globals(self, **globals):
        return attr.evolve(self, globals=self._globals.update(globals))

    def needs(self, assets):
        """
        Wrap the decorated callable to include the given assets when called.

        Arguments:

            assets (iterable):

                the needed asset names
        """

        def _needs(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                if args:
                    request = args[0]
                else:
                    request = kwargs.get("request")
                kwargs.update(
                    (name, self.provide(name, request=request))
                    for name in assets
                    if name not in kwargs
                )
                return fn(*args, **kwargs)
            return wrapped
        return _needs

    def provide(self, name, request=None):
        """
        Provide the given asset.

        """

        asset = self._globals.get(name)
        if asset is not None:
            return asset

        if name not in self._assets:
            raise NoSuchAsset(name)

        if request is None:
            raise TypeError(
                "The {0!r} asset needs a request!".format(name)
            )

        state = self._manager._requests[id(request)]["assets"]

        if name in state:
            asset = state[name]
        else:
            provider = self._assets[name]

            if name in self._needs_request:
                asset = state[name] = provider(request)
            else:
                asset = state[name] = provider()

        return asset

    def remove(self, asset):
        """
        Remove the given asset from the bin.

        """

        self._needs_request = self._needs_request.discard(asset)
        self._assets = self._assets.discard(asset)
        self._globals = self._globals.discard(asset)

    def update(self, bin):
        """
        Add the given bin into this one.

        """

        self._needs_request = self._needs_request.update(bin._needs_request)
        self._assets = self._assets.update(bin._assets)
        self._globals = self._globals.update(bin._globals)
