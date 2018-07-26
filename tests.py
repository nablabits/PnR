import unittest
import pnr
import os
import records
from datetime import date, datetime, timedelta


class TestOrigins(unittest.TestCase):
    """Test the file and the db."""

    def setUp(self):
        """Get the test working."""
        self.df = pnr.TrackDB()
        self.path = self.df.GetPath()

    def test_path_exists(self):
        """Getpath returns a valid path."""
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


class TestData(unittest.TestCase):
    """Test the data from the db."""

    def setUp(self):
        """Get the test working."""
        self.df = pnr.DataYear()

    def test_last_entries_outputs_a_RecordCollection(self):
        """LastEntriesQuery() must output a class RecordCollection."""
        today = date.today()
        df = self.df.LastEntriesQuery(today)
        self.assertIsInstance(df, records.RecordCollection)

    def test_last_entries_are_from_the_same_day(self):
        today = date.today()
        df = self.df.LastEntriesQuery(today)
        for entry in df:
            self.assertEqual(entry.started, str(today))

    def test_period_year_outputs_jan_first(self):
        period_fn = self.df.Period(period='year')
        self.assertEqual(period_fn, '\'2018-01-01\'')

    def test_period_week_outputs_jan_first(self):
        period_fn = self.df.Period(period='week')
        delta = timedelta(days=-1)
        start = date.today()
        while start.isocalendar()[2] != 1:  # reduce days until reach mon
            start = start + delta
        period = '\'' + str(start) + '\''
        self.assertEqual(period_fn, period)

    def test_period_custom_outputs_date_string_quoted(self):
        custom_date = date(2018, 3, 5)
        period_fn = self.df.Period(period=custom_date)
        period = '\'' + str(custom_date) + '\''
        self.assertEqual(period_fn, period)

    def test_invalid_period_outputs_jan_first(self):
        period_fn = self.df.Period(period='invalid period')
        self.assertEqual(period_fn, '\'2018-01-01\'')

    def test_tags_outputs_a_dict_element(self):
        tags = self.df.Tags(period='year')
        self.assertIsInstance(tags, dict)

    def test_tags_dict_keys_are_strings(self):
        tags = self.df.Tags(period='year')
        for i in tags:
            self.assertIsInstance(i, str)

    def test_tags_dict_values_are_floats(self):
        tags = self.df.Tags(period='year')
        for i in tags:
            self.assertIsInstance(tags[i], float)

    def test_tags_dict_values_are_positive(self):
        tags = self.df.Tags(period='year')
        for i in tags:
            self.assertGreaterEqual(tags[i], 0)

    def test_project_outputs_a_dict_element(self):
        projects = self.df.Project(period='year')
        self.assertIsInstance(projects, dict)

    def test_project_dict_keys_are_strings(self):
        projects = self.df.Project(period='year')
        for i in projects:
            self.assertIsInstance(i, str)

    def test_project_dict_values_are_floats(self):
        projects = self.df.Project(period='year')
        for i in projects:
            self.assertIsInstance(projects[i], float)

    def test_project_dict_values_are_positive(self):
        projects = self.df.Project(period='year')
        for i in projects:
            self.assertGreaterEqual(projects[i], 0)

    def test_projectday_returns_a_list(self):
        start = date(2018, 1, 1)
        daylist = pnr.Graph.DayList()
        project_day = self.df.ProjectDay(start, 38, daylist)
        self.assertIsInstance(project_day, list)

# class TestFilters(unittest.TestCase):
#     """Test the filters for the data extacted."""
#
#     def setUp(self):
#         """Get the test working."""
#         db = pnr.DataYear()
#         self.year_data = db.Year()
#         labels = db.Labels()
#         self.filter = pnr.Filters(labels)
#
#     def test_filters_output_a_Record_list(self):
#         """Every filter must output a list of Records, so other filters can be
#         applied later on.
#         """
#         week = self.filter.WeekFilter(self.year_data)
#         label = self.filter.LabelFilter(self.year_data, 'BuildUp')
#         project = self.filter.ProjectFilter(self.year_data, 21)
#
#         # Now, they sould be an object records.Record
#         for row in week:
#             self.assertIsInstance(row, records.Record)
#         for row in label:
#             self.assertIsInstance(row, records.Record)
#         for row in project:
#             self.assertIsInstance(row, records.Record)
#
#     def test_filters_can_be_applied_in_any_order(self):
#         """Filters can be applied in any order & they must return the same."""
#         way1 = self.filter.WeekFilter(self.year_data)
#         way1 = self.filter.LabelFilter(way1, 'BuildUp')
#
#         way2 = self.filter.LabelFilter(self.year_data, 'BuildUp')
#         way2 = self.filter.WeekFilter(way2)
#
#         self.assertEqual(way1, way2)
#
#     def test_dayFilter_outputs_given_day_results(self):
#         """Only given day results are allowed."""
#         day = date(2018, 2, 3)
#         df = self.filter.DayFilter(self.year_data, day)
#         df_check = True
#         for entry in df:
#             curr_date = datetime.strptime(entry.started, '%Y-%m-%d').date()
#             if curr_date != day:
#                 df_check = False
#         self.assertTrue(df_check)
#
#
# class TestLastEntries(unittest.TestCase):
#     """Tests related to the last entries."""
#
#     def setUp(self):
#         """Get the test working."""
#         db = pnr.DataYear()
#         df = db.Year()
#         labels = db.Labels()
#         filters = pnr.Filters(labels)
#         self.lst_entr = pnr.LastEntries(df, filters, days=3)
#
#     def test_DateList_outputs_a_list_of_date_objects(self):
#         """The output for DateList should be a collection of date obj."""
#         date_list = self.lst_entr.DateList()
#         for entry in date_list:
#             self.assertIsInstance(entry, date)
#
#     def test_DataFrame_outputs_a_RecordCollection(self):
#         """The output for DataFrame should be a list of record obj."""
#         DataFrame = self.lst_entr.DataFrame()
#         for row in DataFrame:
#             self.assertIsInstance(row, list)
#             for entry in row:
#                 self.assertIsInstance(entry, records.Record)


# class TestWeek(unittest.TestCase):
#     pass
#
#
# class TestBackup(unittest.TestCase):
#     pass

if __name__ == '__main__':
    unittest.main()
