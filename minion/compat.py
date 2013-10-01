from operator import methodcaller
import sys


PY3 = sys.version_info[0] >= 3


if PY3:
    from urllib.parse import urlencode
    iteritems = methodcaller("items")
else:
    from urllib import urlencode
    iteritems = methodcaller("iteritems")
