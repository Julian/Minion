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
        self._needs_request = set()
        self.globals = dict(globals)

    def __contains__(self, resource):
        return resource in self._resources or resource in self.globals

    @property
    def resources(self):
        return viewkeys(self._resources) | viewkeys(self.globals)

    def provides(self, resource, needs_request=False):
        """
        Declare that the decorated callable provides the given resource.

        :argument str resource: the name of the new resource
        :argument bool needs_request: whether to pass the request in to the
            given callable when calling it

        """

        def _provides(fn):
            if resource in self:
                raise DuplicateResource(resource)
            self._resources[resource] = fn

            if needs_request:
                self._needs_request.add(resource)

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
                if args:
                    request = args[0]
                else:
                    request = kwargs.get("request")
                kwargs.update(
                    (name, self.provide(name, request=request))
                    for name in resources
                    if name not in kwargs
                )
                return fn(*args, **kwargs)
            return wrapped
        return _needs

    def provide(self, name, request=None):
        """
        Provide the given resource.

        """

        resource = self.globals.get(name)
        if resource is not None:
            return resource

        if name not in self._resources:
            raise NoSuchResource(name)

        if request is None:
            raise TypeError(
                "The {0!r} resource needs a request!".format(name)
            )

        state = self._manager.requests[request]["resources"]

        if name in state:
            resource = state[name]
        else:
            provider = self._resources[name]

            if name in self._needs_request:
                resource = state[name] = provider(request)
            else:
                resource = state[name] = provider()

        return resource

    def remove(self, resource):
        """
        Remove the given resource from the bin.

        """

        self._needs_request.discard(resource)
        self._resources.pop(resource, None)
        self.globals.pop(resource, None)

    def update(self, bin):
        """
        Add the given bin into this one.

        """

        self._needs_request.update(bin._needs_request)
        self._resources.update(bin._resources)
        self.globals.update(bin.globals)
