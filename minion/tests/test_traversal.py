from unittest import TestCase

from minion import traversal
from minion.http import URL
from minion.request import Request, Response


def path_view(request):
    """
    A renderer (view) that returns a response with the request path.

    Optionally adds a prefix to the front.

    """

    return Response(content=request.url.path)


class TestTreeResource(TestCase):
    def test_it_renders_what_its_told(self):
        resource = traversal.TreeResource(render=path_view)
        request = Request(url=URL(path=b"/bar"))
        self.assertEqual(resource.render(request), Response(content=b"/bar"))

    def test_it_supports_adding_children(self):
        resource = traversal.TreeResource(render=path_view)
        child = traversal.LeafResource(render=path_view)
        resource.set_child(b"foo", child)
        request = Request(url=URL(path=b"/bar"))
        self.assertEqual(resource.get_child(b"foo", request=request), child)

    def test_it_returns_404s_for_unknown_children(self):
        resource = traversal.TreeResource(render=path_view)
        request = Request(url=URL(path=b"/foo"))
        child = resource.get_child(b"foo", request=request)
        self.assertEqual(child.render(request), Response(code=404))


class TestLeafResource(TestCase):
    def test_it_renders_what_its_told(self):
        resource = traversal.LeafResource(
            render=lambda request : Response(content=request.url.path)
        )
        request = Request(url=URL(path=b"/foo"))
        self.assertEqual(resource.render(request), Response(content=b"/foo"))

    def test_it_is_a_leaf_resource(self):
        self.assertTrue(
            traversal.LeafResource(render=lambda request : Response()).is_leaf,
        )


class TestMethodDelegate(TestCase):
    def test_known_HTTP_methods_use_associated_renderer(self):
        render = traversal.method_delegate(
            GET=lambda request : b"foo",
            put=lambda request : request.method,
        )
        get = Request(url=URL(path=b"/"), method=b"GET")
        self.assertEqual(render(get), b"foo")

        put = Request(url=URL(path=b"/"), method=b"PUT")
        self.assertEqual(render(put), b"PUT")

    def test_unknown_HTTP_methods_return_405s(self):
        render = traversal.method_delegate(get=lambda _ : b"foo")
        request = Request(url=URL(path=b"/"), method=b"PUT")
        self.assertEqual(render(request).code, 405)


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
        request = Request(url=URL(path=b"/foo/bar/baz"))
        renderer = traversal.traverse(
            path=b"/foo/bar/baz", resource=root, request=request,
        )
        self.assertEqual(renderer.render(request), b"foo\nbar\nbaz")

    def test_single_level(self):
        root = LineDelimiterResource()
        request = Request(url=URL(path=b"/foo"))
        renderer = traversal.traverse(
            path=b"/foo", resource=root, request=request,
        )
        self.assertEqual(renderer.render(request), b"foo")

    def test_zero_levels(self):
        root = LineDelimiterResource()
        request = Request(url=URL(path=b"/"))
        renderer = traversal.traverse(
            path=b"/", resource=root, request=request,
        )
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
        request = Request(url=URL(path=b"/0/1/2/3/4/5"))
        renderer = traversal.traverse(
            path=b"/0/1/2/3/4/5", resource=root, request=request,
        )
        self.assertEqual(renderer.render(request), b"2")
