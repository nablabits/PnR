import unittest
import pnr_v2 as pnr
import os


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


class TestOrigins(unittest.TestCase):
    """Test the file and the db."""

    def setUp(self):
        self.df = pnr.TrackDB()
        self.path = self.df.GetPath()

    # def tearDown(self):
    #     self.df.CleanUp()

    def test_path_exists(self):
        """Getpath returns a valid path."""
        # path = self.df.GetPath()
        path = self.path

        self.assertTrue(os.path.isdir(path))

    def test_file_exists(self):
        """Getfile returns a valid file."""
        zipfile = self.df.GetFile()
        path = self.path
        zipfile = path + zipfile
        self.assertTrue(os.path.isfile(zipfile))

    def test_filecheck_false(self):
        """Filecheck returns false when there's no tmp folder."""
        filecheck = self.df.FileCheck()
        self.assertFalse(filecheck)

    def test_filecheck_folder_zipfile_false(self):
        """Returns false when zipfile is more recent than folder."""
        path = self.path
        filecheck = self.df.FileCheck()
        os.mkdir(path + 'tmp/')
        os.chdir(path)
        with open('examplezip.zip', 'w'):
            pass
        self.assertFalse(filecheck)
        os.rmdir('tmp/')
        os.unlink('examplezip.zip')

    def test_filecheck_folder_zipfile_true(self):
        """Returns true when folder is more recent than zipfile."""
        path = self.path
        filecheck = self.df.FileCheck()
        os.mkdir(path + 'tmp/')
        os.chdir(path)
        self.assertFalse(filecheck)
        os.rmdir('tmp/')

    def test_getdb_returns_a_valid_file(self):
        """Returns true if dbfile exists."""
        dbfile = self.df.GetDB()
        self.assertTrue(os.path.isfile(dbfile))

    def test_cleanup_cleans_tmp(self):
        """Returns false if tmp folder exists after removing."""
        path = self.path
        path = path + 'tmp/'
        if not os.path.isdir(path):
            os.mkdir(path)
        self.df.CleanUp()
        self.assertFalse(os.path.isdir(path))

if __name__ == '__main__':
    unittest.main()
