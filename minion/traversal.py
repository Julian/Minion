"""
Helpers for applications that use object traversal routing.

"""

from future.utils import PY3, iteritems
import attr

from minion.request import Response


@attr.s
class LeafResource(object):
    """
    A leaf resource that simply renders via a provided view.

    """

    is_leaf = True
    render = attr.ib()


@attr.s
class TreeResource(object):
    """
    A tree resource that supports adding children via :meth:`set_child`\ .

    """

    render = attr.ib()
    _children = attr.ib(default=attr.Factory(dict))

    _no_such_child = LeafResource(render=lambda request: Response(code=404))

    def get_child(self, name, request):
        child = self._children.get(name)
        if child is None:
            return self._no_such_child
        return child

    def set_child(self, name, resource):
        self._children[name] = resource


def method_delegate(**methods):
    """
    Construct a renderer that delegates based on the request's HTTP method.

    """

    methods = {k.upper(): v for k, v in iteritems(methods)}

    if PY3:
        methods = {k.encode("utf-8"): v for k, v in iteritems(methods)}

    def render(request):
        renderer = methods.get(request.method)
        if renderer is None:
            return Response(code=405)
        return renderer(request)
    return render


def traverse(path, request, resource):
    """
    Traverse a root resource, retrieving the appropriate child for the request.

    """

    path = path.lstrip(b"/")
    for component in path and path.split(b"/"):
        if getattr(resource, "is_leaf", False):
            break
        resource = resource.get_child(name=component, request=request)
    return resource
