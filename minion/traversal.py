"""
Helpers for applications that use object traversal routing.

"""

class TreeResource(object):
    """
    A tree resource that supports adding children via :meth:`put_child`\ .

    """

    def __init__(self, render):
        self.children = {}
        self.render = render

    def get_child(self, name, request):
        return self.children[name]

    def set_child(self, name, resource):
        self.children[name] = resource


class LeafResource(object):
    """
    A leaf resource that simply renders via a provided view.

    """

    is_leaf = True

    def __init__(self, render):
        self.render = render


def traverse(request, resource):
    """
    Traverse a root resource, retrieving the appropriate child for the request.

    """

    path = request.path.lstrip(b"/")
    for component in path and path.split(b"/"):
        if getattr(resource, "is_leaf", False):
            break
        resource = resource.get_child(name=component, request=request)
    return resource
