import unittest
import os
import re
import zipfile
from pnr import TrackDB


class TestTrackDB(unittest.TestCase):
    def setUp(self):
        tdb = TrackDB()
        self.path = tdb.GetPath()
        self.zipfile = tdb.GetFile()

        # Set up newest test
        file_timelist = []
        file_namelist = []
        for entry in os.scandir(self.path):
            if re.search(r'.zip', entry.name):
                file_timelist.append(entry.stat().st_mtime)
                file_namelist.append(entry.name)
        max_idx = file_timelist.index(max(file_timelist))
        self.entry_idx = file_namelist[max_idx]

    def test_path_exists(self):
        """Test if path exists & is a dir."""
        self.assertTrue(os.path.isdir(self.path))

    def test_file_exists(self):
        """Test if file exists in the selected path."""
        self.assertTrue(zipfile.is_zipfile(self.path+self.zipfile))

    def test_file_is_the_newest(self):
        """Test if the selected file is the newest."""
        self.assertEqual(self.zipfile, self.entry_idx)

    def test_db_file_exists(self):
        """Test if the extracted file exists."""
        tdb = TrackDB()
        self.dbfile = tdb.XtractFile()
        self.assertTrue(os.path.isfile(self.dbfile))


# class TestQueries(unittest.TestCase):
#     raise NameError('must continue here')


if __name__ == '__main__':
    unittest.main()
