"""
Helpers and utilities for testing Minion applications.

Unlike the rest of the test modules, this module *is* public API.

"""

class ResponseHelpersMixin(object):
    def assertRedirected(self, response, to, code=302):
        """
        Assert that the given response is a redirect to the given URL.

        """

        self.assertEqual(response.code, code)
        self.assertIn("Location", response.headers)
        self.assertEqual(response.headers.get("Location")[0], to)
