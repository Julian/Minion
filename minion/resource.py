from functools import wraps


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
        return self._resources.viewkeys()

    def provides(self, resource):
        """
        Declare that the decorated callable provides the given resource.

        :argument str resource: the name of the new resource

        """

        def _provides(fn):
            self._resources[resource] = fn
            return fn
        return _provides

    def needs(self, resources):
        """
        Wrap the decorated callable to include the given resources when called.

        :argument iterable resources: the needed resource names

        """

        global_resources, to_create = [], []

        for name in resources:
            if name in self.globals:
                global_resources.append((name, self.globals[name]))
            elif name in self._resources:
                to_create.append((name, self._resources[name]))
            else:
                raise NoSuchResource(name)

        def _needs(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                kwargs.update(
                    (name, resource) for name, resource in global_resources
                    if name not in kwargs
                )
                kwargs.update(
                    (name, create()) for name, create in to_create
                    if name not in kwargs
                )
                return fn(*args, **kwargs)
            return wrapped
        return _needs
