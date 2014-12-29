from unittest import TestCase
import mock

from minion import request
from minion.http import Accept, Headers, URL
from minion.tests.utils import ResponseHelpersMixin


class TestResponder(TestCase):
    def setUp(self):
        self.request = mock.Mock()
        self.responder = request.Responder(request=self.request)

    def test_it_runs_deferreds_registered_with_after(self):
        m = mock.Mock()
        self.responder.after().on_success(m)
        self.assertFalse(m.called)

        self.responder.finish()

        m.assert_called_once_with(self.responder)


class TestManager(TestCase):
    def setUp(self):
        self.manager = request.Manager()
        self.request = mock.Mock()
        self.response = mock.Mock()

    def test_after_response(self):
        self.manager.request_started(self.request)
        callback = mock.Mock(return_value=None)

        self.manager.after_response(self.request, callback, 1, kw="abc")

        response = self.manager.request_served(self.request, self.response)

        self.assertEqual(response, self.response)
        callback.assert_called_once_with(self.response, 1, kw="abc")

    def test_after_response_can_modify_the_response(self):
        new_response = mock.Mock()

        self.manager.request_started(self.request)
        def set_thing(response):
            return new_response

        self.manager.after_response(self.request, set_thing)

        response = self.manager.request_served(self.request, self.response)

        self.assertEqual(response, new_response)

    def test_after_response_chaining(self):
        self.manager.request_started(self.request)
        def set_thing(response):
            response.thing = 2

        def add_2(response):
            response.thing += 2

        self.manager.after_response(self.request, set_thing)
        self.manager.after_response(self.request, add_2)

        response = self.manager.request_served(self.request, self.response)

        self.assertEqual(response, self.response)
        self.assertEqual(response.thing, 4)


class RequestTestMixin(object):
    """
    Tests implementations of the Request interface.

    """

    def test_accept(self):
        accept = "application/json"
        request = self.make_request(headers=Headers([("accept", [accept])]))
        self.assertEqual(request.accept, Accept.from_header(accept))

    def test_accept_no_header(self):
        request = self.make_request(headers=Headers())
        self.assertEqual(request.accept, Accept.ALL)

    def test_accept_is_calculated_once(self):
        accept = "application/json"
        request = self.make_request(headers=Headers([("accept", [accept])]))
        self.assertIs(request.accept, request.accept)


class TestRequest(RequestTestMixin, TestCase):
    def make_request(self, headers):
        return request.Request(url=URL(path=b"/"), headers=headers)

    def test_url(self):
        self.request = request.Request(url=URL(path=b"/foo/bar"))
        self.assertEqual(self.request.url, URL(path=b"/foo/bar"))

    def test_flash(self):
        self.request = request.Request(url=URL(path=b"/"))
        self.assertEqual(self.request.messages, [])
        self.request.flash(b"Hello World")
        self.assertEqual(
            self.request.messages, [request._Message(content=b"Hello World")],
        )


class TestResponse(TestCase):
    def test_init(self):
        self.assertEqual(request.Response(b"Hello").content, b"Hello")

    def test_init_kwargs(self):
        self.assertEqual(request.Response(content=b"Hello").content, b"Hello")


class TestRedirect(ResponseHelpersMixin, TestCase):
    def test_it_returns_redirect_responses(self):
        response = request.redirect(to="http://example.com")
        self.assertRedirected(response, "http://example.com")

    def test_it_allows_specifying_a_status_code(self):
        response = request.redirect(to="http://example.com", code=304)
        self.assertRedirected(response, "http://example.com", code=304)
