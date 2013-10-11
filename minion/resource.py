from functools import wraps

from minion.compat import viewkeys


class DuplicateResource(Exception):
    pass


class NoSuchResource(LookupError):
    pass


class Bin(object):
    def __init__(self, manager, globals=()):
        self._manager = manager
        self._resources = {}
        self.globals = dict(globals)

    def __contains__(self, resource):
        return resource in self._resources or resource in self.globals

    @property
    def resources(self):
        return viewkeys(self._resources) | viewkeys(self.globals)

    def provides(self, resource):
        """
        Declare that the decorated callable provides the given resource.

        :argument str resource: the name of the new resource

        """

        def _provides(fn):
            if resource in self:
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
            def wrapped(request, *args, **kwargs):
                for resource_name in resources:
                    if resource_name in kwargs:
                        continue
                    elif resource_name in self.globals:
                        kwargs[resource_name] = self.globals[resource_name]
                    elif resource_name in self._resources:
                        state = self._manager.requests[request]["resources"]

                        if resource_name in state:
                            resource = state[resource_name]
                        else:
                            provider = self._resources[resource_name]
                            resource = state[resource_name] = provider(request)

                        kwargs[resource_name] = resource
                    else:
                        raise NoSuchResource(resource_name)
                return fn(request, *args, **kwargs)
            return wrapped
        return _needs

    def remove(self, resource):
        """
        Remove the given resource from the bin.

        """

        self._resources.pop(resource, None)
        self.globals.pop(resource, None)

    def update(self, bin):
        """
        Add the given bin into this one.

        """

        self._resources.update(bin._resources)
        self.globals.update(bin.globals)
