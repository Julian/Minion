_NOTHING_YET = object()


class Deferred(object):
    """
    A coordinator of a future result.

    """

    def __init__(self):
        chain = _CallbackChain()
        self.chain = chain
        self.succeed = chain._succeed

    def error(self, result):
        """
        Report having failed with the given error.

        """

        self.chain._error(result=result)


class _CallbackChain(object):
    """
    A callback chain manages a collection of success- and error- handlers.

    """

    _resulted_in = _NOTHING_YET

    def __init__(self):
        self._callbacks = []

    def on_success(self, fn, *args, **kwargs):
        """
        Call the given callback if or when the connected deferred succeeds.

        """

        self._callbacks.append((fn, args, kwargs))

        result = self._resulted_in
        if result is not _NOTHING_YET:
            self._succeed(result=result)

    def on_error(self, fn, *args, **kwargs):
        """
        Call the given callback if or when the connected deferred errors.

        """

    def _succeed(self, result):
        """
        Fire the success chain.

        """

        for fn, args, kwargs in self._callbacks:
            fn(result, *args, **kwargs)
        self._resulted_in = result
