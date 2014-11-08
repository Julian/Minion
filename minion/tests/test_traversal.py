from unittest import TestCase

from minion import traversal
from minion.request import Request, Response


class TestLeafResource(TestCase):
    def test_it_renders_what_its_told(self):
        resource = traversal.LeafResource(
            render=lambda request : Response(content=request.path)
        )
        request = Request(path=b"/foo")
        self.assertEqual(resource.render(request), Response(content=b"/foo"))

    def test_it_is_a_leaf_resource(self):
        self.assertTrue(
            traversal.LeafResource(render=lambda request : Response()).is_leaf,
        )


class LineDelimiterResource(object):
    """
    A resource where traversal returns a child resource that renders the
    ultimate path as a line delimited bytestring.

    """

    def __init__(self, path=()):
        self.path = list(path)

    def get_child(self, name, request):
        return self.__class__(path=self.path + [name])

    def render(self, request):
        return b"\n".join(self.path)


class TestTraverse(TestCase):
    def test_it_traverses_resources(self):
        root = LineDelimiterResource()
        request = Request(path="/foo/bar/baz")
        renderer = traversal.traverse(resource=root, request=request)
        self.assertEqual(renderer.render(request), "foo\nbar\nbaz")

    def test_single_level(self):
        root = LineDelimiterResource()
        request = Request(path="/foo")
        renderer = traversal.traverse(resource=root, request=request)
        self.assertEqual(renderer.render(request), "foo")

    def test_zero_levels(self):
        root = LineDelimiterResource()
        request = Request(path="/")
        renderer = traversal.traverse(resource=root, request=request)
        self.assertIs(renderer, root)

    def test_leaf_resources_are_not_traversed(self):
        class Resource(object):
            def __init__(self, name=b""):
                self.name = name

            def get_child(self, name, request):
                resource = Resource(name=name)
                if name == b"2":
                    resource.is_leaf = True
                return resource

            def render(self, name):
                return self.name

        root = Resource()
        request = Request(path="/0/1/2/3/4/5")
        renderer = traversal.traverse(resource=root, request=request)
        self.assertEqual(renderer.render(request), "2")
