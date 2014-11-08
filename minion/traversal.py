"""
Helpers for applications that use object traversal routing.

"""

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

    path = request.path.lstrip("/")
    for component in path and path.split("/"):
        if getattr(resource, "is_leaf", False):
            break
        resource = resource.get_child(name=component, request=request)
    return resource
