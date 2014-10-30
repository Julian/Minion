from unittest import TestCase

from minion.http import Headers
from minion.request import Response
from minion.tests import utils


class TestResponseHelpersMixin(utils.ResponseHelpersMixin, TestCase):
    def test_assertRedirected_succeeds_for_redirects(self):
        response = Response(
            headers=Headers([("Location", ["http://example.com"])]), code=302,
        )
        self.assertRedirected(response, to="http://example.com", code=302)

    def test_assertRedirected_fails_for_mismatched_urls(self):
        response = Response(
            headers=Headers([("Location", ["http://example.com"])]), code=302,
        )
        with self.assertRaises(self.failureException):
            self.assertRedirected(response, to="http://other.com", code=302)

    def test_assertRedirected_fails_for_mismatched_code(self):
        response = Response(
            headers=Headers([("Location", ["http://example.com"])]), code=301,
        )
        with self.assertRaises(self.failureException):
            self.assertRedirected(response, to="http://example.com", code=302)

    def test_assertRedirected_fails_for_non_redirects(self):
        response = Response()
        with self.assertRaises(self.failureException):
            self.assertRedirected(response, to="http://example.com", code=302)

    def test_assertRedirected_assumes_a_302(self):
        response = Response(
            headers=Headers([("Location", ["http://example.com"])]), code=302,
        )
        self.assertRedirected(response, to="http://example.com")
