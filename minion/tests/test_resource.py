from unittest import TestCase
import mock

from minion import resource


class TestResourceBin(TestCase):
    def setUp(self):
        self.bin = resource.Bin()
        self.fn = mock.Mock(__name__="a_view")

    def test_it_stores_resources(self):
        @self.bin.provides("iron")
        def make_iron():
            return 12

        returned = self.bin.needs(["iron"])(self.fn)(1, "foo", bar=3)

        self.assertIs(returned, self.fn.return_value)
        self.fn.assert_called_once_with(1, "foo", bar=3, iron=12)

    def test_multiple_needs(self):
        @self.bin.provides("iron")
        def make_iron():
            return 12

        thing = mock.Mock()
        @self.bin.provides("wine")
        def make_wine():
            return thing

        self.bin.needs(["wine", "iron"])(self.fn)(1)

        self.fn.assert_called_once_with(1, iron=12, wine=thing)
