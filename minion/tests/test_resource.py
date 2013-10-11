from unittest import TestCase
import mock

from minion import resource


class TestResourceBin(TestCase):
    def setUp(self):
        self.bin = resource.Bin()
        self.fn = mock.Mock(__name__="a_view")
        self.request = mock.Mock()

    def test_it_contains_resources(self):
        self.assertNotIn("cheese", self.bin)

        @self.bin.provides("cheese")
        def make_cheese():
            return "Gouda"

        self.assertIn("cheese", self.bin)

    def test_it_contains_globals(self):
        self.assertNotIn("cheese", self.bin)
        self.bin.globals["cheese"] = 12
        self.assertIn("cheese", self.bin)

    def test_it_provides_resources_to_things_that_need_them(self):
        @self.bin.provides("iron")
        def make_iron(request):
            return 12

        returned = self.bin.needs(["iron"])(self.fn)(self.request, 1, bar=3)

        self.assertIs(returned, self.fn.return_value)
        self.fn.assert_called_once_with(self.request, 1, bar=3, iron=12)

    def test_it_provides_a_new_resource_instance_each_time(self):
        fn = self.bin.needs(["sugar"])(self.fn)
        sugar = mock.Mock()
        self.bin.provides("sugar")(sugar)
        fn(self.request)
        fn(self.request)
        self.assertEqual(sugar.call_count, 2)

    def test_multiple_needs(self):
        @self.bin.provides("iron")
        def make_iron(request):
            return 12

        thing = mock.Mock()
        @self.bin.provides("wine")
        def make_wine(request):
            return thing

        self.bin.needs(["wine", "iron"])(self.fn)(self.request)

        self.fn.assert_called_once_with(self.request, iron=12, wine=thing)

    def test_it_provides_only_unprovided_resources(self):
        """
        It should still be possible to pass in arguments if desired.

        """

        @self.bin.provides("iron")
        def make_iron(request):
            return 12

        self.bin.globals["cheese"] = 18
        self.bin.globals["wine"] = 13

        self.bin.needs(["wine", "iron", "cheese"])(self.fn)(
            self.request, iron=24, wine=1,
        )

        self.fn.assert_called_once_with(
            self.request, cheese=18, iron=24, wine=1,
        )

    def test_it_provides_globals(self):
        self.assertEqual(self.bin.globals, {})
        important = self.bin.globals["important"] = mock.Mock()
        self.bin.needs(["important"])(self.fn)(self.request)
        self.fn.assert_called_once_with(self.request, important=important)

    def test_it_knows_its_resources(self):
        self.bin.provides("milk")(mock.Mock())
        self.bin.provides("honey")(mock.Mock())
        self.bin.globals["gold"] = mock.Mock()
        self.assertEqual(self.bin.resources, {"milk", "honey", "gold"})

    def test_a_non_existent_resource_raises_an_exception_when_called(self):
        fn = self.bin.needs(["iron"])(self.fn)

        with self.assertRaises(resource.NoSuchResource) as e:
            fn(self.request)
        self.assertEqual(e.exception.args, ("iron",))

    def test_resources_can_be_created_right_before_call_time(self):
        """
        A resource provision can be done after declaring something needs it.

        """

        fn = self.bin.needs(["cake"])(self.fn)
        cake = mock.Mock()
        self.bin.provides("cake")(cake)
        fn(self.request)
        self.fn.assert_called_once_with(self.request, cake=cake.return_value)

    def test_remove(self):
        self.bin.provides("gold")(mock.Mock())
        self.assertIn("gold", self.bin)
        self.bin.remove("gold")
        self.assertNotIn("gold", self.bin)

    def test_remove_global(self):
        self.bin.globals["silver"] = mock.Mock()
        self.assertIn("silver", self.bin)
        self.bin.remove("silver")
        self.assertNotIn("silver", self.bin)

    def test_quashing_an_existing_resource_raises_an_exception(self):
        self.bin.provides("iron")(mock.Mock())
        with self.assertRaises(resource.DuplicateResource):
            self.bin.provides("iron")(mock.Mock())

    def test_quashing_an_existing_global_raises_an_exception(self):
        self.bin.globals["iron"] = mock.Mock()
        with self.assertRaises(resource.DuplicateResource):
            self.bin.provides("iron")(mock.Mock())

    def test_update(self):
        iron, wine = mock.Mock(), mock.Mock()

        self.bin.provides("iron")(iron)
        self.bin.provides("wine")(wine)

        gold = mock.Mock()
        bin = resource.Bin(globals={"gold" : gold})

        self.bin.update(bin)

        self.assertEqual(self.bin.resources, {"iron", "wine", "gold"})
