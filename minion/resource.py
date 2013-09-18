from functools import wraps


class Bin(object):
    def __init__(self):
        self._resources = {}

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

        def _needs(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                kwargs.update(
                    (resource, self._resources[resource]())
                    for resource in resources
                )
                return fn(*args, **kwargs)
            return wrapped
        return _needs
