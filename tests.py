import unittest
import pnr_v2 as pnr


class TestUtils(unittest.TestCase):
    """Test utils."""

    def setUp(self):
        self.utils = pnr.Utils()
        self.numberlist = (12, 15, 25, 70)

    def test_binary_finds_number(self):
        """Binary search finds the number."""
        numberlist = self.numberlist
        number = 25
        result = self.utils.binary(numberlist, number)
        self.assertTrue(result[0])

    def test_binary_exclude_number(self):
        """Binary search returns False with numbers not within list."""
        numberlist = self.numberlist
        number = 26
        result = self.utils.binary(numberlist, number)
        self.assertFalse(result[0])

    def test_binary_high_number(self):
        """Binary search returns False with numbers highers than list."""
        numberlist = self.numberlist
        number = 90
        result = self.utils.binary(numberlist, number)
        self.assertFalse(result[0])

    def test_binary_lo_number(self):
        """Binary search returns False with numbers lowers than list."""
        numberlist = self.numberlist
        number = 5
        result = self.utils.binary(numberlist, number)
        self.assertFalse(result[0])

if __name__ == '__main__':
    unittest.main()
