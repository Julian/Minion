======
Minion
======

    .. epigraph::

        The world needs another web framework.

        -- No one, ever. And yet...


Minion is a microframework that grew out of a collection of individually small
frustrations with `Flask <https://flask.pocoo.org>`_.

Specifically, it aims to be simpler and more composeable than Flask is in the
following ways:

    * Call views with arguments rather than thread locals
    * Allow alternative routing implementations
    * Provide a more robust configuration interface


In some ways it's inspired by `Klein <https://github.com/Twisted/Klein>`_\'s
take on Flask more than Flask's take on Flask.


Example
-------

Here's the Minion hello world:

    .. code-block:: python

        from minion.core import Application
        from minion.request import Response


        app = Application()

        @app.route("/")
        def index(request):
            return Response("Hello World!")


Versioning
----------

Minion uses `SemVer <http://semver.org/>`_.

Specifically, this means that until ``v1.0.0`` Minion is *not*
guaranteed to be backwards compatible, even in minor releases (or bugfix
releases but there probably won't be any of those).

That being said, nothing will be broken for the hell of it :). Make of
that what you will.

After ``v1.0.0``, public API (to be defined later) will not be broken in
backwards incompatible ways without a major version bump.


Contributing
------------

I'm Julian Berman.

``minion`` is on `GitHub <https://github.com/Julian/Minion>`_.

Get in touch, via GitHub or otherwise, if you've got something to contribute,
it'd be most welcome!

You can also generally find me on Freenode (nick: ``tos9``) in various
channels, including ``#python``.

If you feel overwhelmingly grateful, you can woo me with beer money on
`Gittip <https://www.gittip.com/Julian/>`_ or via Google Wallet with the email
in my GitHub profile.
