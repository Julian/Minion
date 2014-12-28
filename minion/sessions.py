try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping


class UnencryptedCookieSession(MutableMapping):
    def __init__(self):
        self._contents = {}

    def __iter__(self):
        return iter(self._contents)

    def __len__(self):
        return len(self._contents)

    def __delitem__(self, key):
        del self._contents[key]

    def __getitem__(self, key):
        return self._contents[key]

    def __setitem__(self, key, value):
        self._contents[key] = value
