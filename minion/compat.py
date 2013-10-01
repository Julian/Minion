from operator import methodcaller
import sys


PY3 = sys.version_info[0] >= 3


if PY3:
    from urllib.parse import urlencode
    iteritems = methodcaller("items")
    items = lambda d : list(d.items())
    viewkeys = methodcaller("keys")
else:
    from urllib import urlencode
    iteritems = methodcaller("iteritems")
    items = methodcaller("items")
    viewkeys = methodcaller("viewkeys")
