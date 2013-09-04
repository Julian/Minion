from unittest import TestCase
import mock

from minion import core
from minion.request import Request
from minion.routers import SimpleRouter


class TestApplication(TestCase):
    def setUp(self):
        self.router = mock.Mock(spec=SimpleRouter())
        self.application = core.Application(router=self.router)

    def test_it_serves_matched_requests(self):
        view, _ = self.router.match.return_value = mock.Mock(), {"foo" : 12}
        request = mock.Mock(spec=Request(path="/"))
        self.application.serve(request)
        view.assert_called_once_with(request, foo=12)

    def test_it_serves_404s_for_unmatched_requests_by_default(self):
        view, _ = self.router.match.return_value = None, {}
        request = mock.Mock(spec=Request(path="/"))
        response = self.application.serve(request)
        self.assertEqual(response.code, 404)
