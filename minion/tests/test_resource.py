from unittest import TestCase
import mock

from minion import resource


class TestResourceBin(TestCase):
    def test_it_stores_resources(self):
        bin = resource.Bin()

        @bin.provides("iron")
        def make_iron():
            return 12

        fn = mock.Mock(__name__="a_view")
        returned = bin.needs(["iron"])(fn)(1, "foo", bar=3)

        self.assertIs(returned, fn.return_value)
        fn.assert_called_once_with(1, "foo", bar=3, iron=12)
