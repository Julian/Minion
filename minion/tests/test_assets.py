from unittest import TestCase

from minion import assets


class TestBin(TestCase):
    def test_it_provides_assets(self):
        bin = assets.Bin().add(twelve=lambda bin: 12)
        self.assertEqual(bin.provide("twelve"), 12)

    def test_no_such_asset(self):
        with self.assertRaises(assets.NoSuchAsset) as e:
            assets.Bin().provide("twelve")
        self.assertEqual(str(e.exception), "twelve")

    def test_hash(self):
        self.assertIn(
            assets.Bin().add(zero=int),
            {assets.Bin().add(zero=int)},
        )

    def test_repr(self):
        self.assertEqual(
            repr(assets.Bin().add(zero=int).add(empty=str)),
            "<Bin: {'empty', 'zero'}>",
        )
