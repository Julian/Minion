from functools import wraps

from minion.compat import viewkeys


class DuplicateResource(Exception):
    pass


class NoSuchResource(LookupError):
    pass


class Bin(object):
    def __init__(self, globals=()):
        self._resources = {}
        self.globals = dict(globals)

    def __contains__(self, resource):
        return resource in self._resources or resource in self.globals

    @property
    def resources(self):
        return viewkeys(self._resources)

    def provides(self, resource):
        """
        Declare that the decorated callable provides the given resource.

        :argument str resource: the name of the new resource

        """

        def _provides(fn):
            if resource in self.resources:
                raise DuplicateResource(resource)
            self._resources[resource] = fn
            return fn
        return _provides

    def needs(self, resources):
        """
        Wrap the decorated callable to include the given resources when called.

        :argument iterable resources: the needed resource names

        """

        def _needs(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                for resource in resources:
                    if resource in kwargs:
                        continue
                    elif resource in self.globals:
                        kwargs[resource] = self.globals[resource]
                    elif resource in self._resources:
                        kwargs[resource] = self._resources[resource]()
                    else:
                        raise NoSuchResource(resource)
                return fn(*args, **kwargs)
            return wrapped
        return _needs

    def remove(self, resource):
        """
        Remove the given resource from the bin.

        """

        self._resources.pop(resource, None)
        self.globals.pop(resource, None)
