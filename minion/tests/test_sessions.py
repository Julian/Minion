from unittest import TestCase

from minion import sessions


class TestUnencryptedCookieSession(TestCase):
    def setUp(self):
        self.session = sessions.UnencryptedCookieSession()

    def test_its_a_mutable_mapping(self):
        self.session["thing"] = 12
        self.assertIn("thing", self.session)
        self.assertNotIn("other", self.session)
        self.assertEqual(self.session["thing"], 12)
