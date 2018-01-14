from pyrsistent import m
import attr


class DuplicateAsset(Exception):
    pass


class NoSuchAsset(LookupError):
    pass


@attr.s(hash=True, repr=False)
class Bin(object):

    _assets = attr.ib(default=m())

    def __repr__(self):
        return "<{}: {{{}}}>".format(
            self.__class__.__name__,
            ", ".join(repr(asset) for asset in sorted(self._assets)),
        )

    def add(self, **assets):
        return attr.evolve(self, assets=self._assets.update(assets))

    def with_globals(self, **kwargs):
        def _global(thing):
            return lambda bin: thing
        return self.add(
            **{name: _global(thing) for name, thing in kwargs.items()}
        )

    def provide(self, name):
        try:
            provider = self._assets[name]
        except KeyError:
            raise NoSuchAsset(name)
        else:
            return provider(bin=self)
