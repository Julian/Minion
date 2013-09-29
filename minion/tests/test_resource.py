from unittest import TestCase
import mock

from minion import resource


class TestResourceBin(TestCase):
    def setUp(self):
        self.bin = resource.Bin()
        self.fn = mock.Mock(__name__="a_view")

    def test_it_contains_resources(self):
        self.assertNotIn("cheese", self.bin)

        @self.bin.provides("cheese")
        def make_cheese():
            return "Gouda"

        self.assertIn("cheese", self.bin)

    def test_it_provides_resources_to_things_that_need_them(self):
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

    def test_it_can_contain_globals(self):
        self.assertEqual(self.bin.globals, {})
        important_thing = self.bin.globals["important_thing"] = mock.Mock()
        self.bin.needs(["important_thing"])(self.fn)()
        self.fn.assert_called_once_with(important_thing=important_thing)

    def test_it_knows_its_resources(self):
        for resource in "milk", "honey", "gold":
            self.bin.provides(resource)(mock.Mock())

        self.assertEqual(self.bin.resources, set(["milk", "honey", "gold"]))
