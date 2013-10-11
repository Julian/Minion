from operator import methodcaller
import sys


PY3 = sys.version_info[0] >= 3


if PY3:
    from collections.abc import MutableMapping
    from urllib.parse import urlencode
    iteritems = viewitems = methodcaller("items")
    items = lambda d : list(d.items())
    viewkeys = methodcaller("keys")
else:
    from collections import MutableMapping
    from urllib import urlencode
    iteritems = methodcaller("iteritems")
    items = methodcaller("items")
    viewkeys = methodcaller("viewkeys")
    viewitems = methodcaller("viewitems")
