from unittest import TestCase, skip

from minion.deferred import Deferred


class ABadThing(Exception):
    pass


class TestDeferred(TestCase):

    success = error = second = None

    def assertResultedIn(self, success=None, error=None, second=None):
        self.assertEqual(
            {"success" : self.success, "error" : self.error},
            {"success" : success, "error" : error},
        )
        self.assertEqual(self.second, second)

    def _succeeded(self, arg, *rest, **kw):
        self.success = (arg,) + rest, kw
        return arg

    def _second_succeeded(self, *args, **kw):
        self.second = args, kw

    def _errored(self, *args, **kw):
        self.error = args, kw

    def test_succeed(self):
        deferred = Deferred()
        deferred.chain.on_success(self._succeeded, "world", end="!")
        deferred.succeed("hello")
        self.assertResultedIn(success=(("hello", "world"), {"end" : "!"}))

    def test_succeed_without_args(self):
        deferred = Deferred()
        deferred.chain.on_success(self._succeeded)
        deferred.succeed("hello")
        self.assertResultedIn(success=(("hello",), {}))

    def test_two_on_successes(self):
        deferred = Deferred()
        deferred.chain.on_success(self._succeeded)
        deferred.chain.on_success(self._second_succeeded)
        deferred.succeed("hello")
        result = (("hello",), {})
        self.assertResultedIn(success=result, second=result)

    def test_immediate_on_success(self):
        deferred = Deferred()
        deferred.succeed("hello")
        deferred.chain.on_success(self._succeeded)
        self.assertResultedIn(success=(("hello",), {}))

    @skip("No errback support yet")
    def test_error(self):
        deferred = Deferred()
        deferred.chain.on_error(self._errored)
        error = ABadThing("Whoops!")
        deferred.error(error)
        self.assertResultedIn(error=((error,), {}))
