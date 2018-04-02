"""This script provides useful data for final day's summary.

Perform a backup of the files as well.
"""
import tarfile
import os
import re
import shutil
from zipfile import ZipFile
import records
from datetime import date, datetime, timedelta, time
from matplotlib import pyplot as plt


class TrackDB:
    """Get the last db file & unpack it into a tmp folder."""

    def GetPath(self):
        """Select te path to the db file. Try first default."""
        default = '/home/davif/Dropbox/Aplicaciones/Swipetimes Time Tracker/'
        zip_dir = os.path.isdir(default)
        while zip_dir is False:
            default = input('Couldn\'t find that location, choose manually: ')
            zip_dir = os.path.isdir(default)
        return default

    def GetFile(self):
        """Get the last zip file from the path."""
        path = self.GetPath()
        file_namelist = []
        file_timelist = []
        for entry in os.scandir(path):
            if re.search(r'.zip', entry.name):
                file_timelist.append(entry.stat().st_mtime)
                file_namelist.append(entry.name)
        max_idx = file_timelist.index(max(file_timelist))
        zipfile = file_namelist[max_idx]
        return zipfile

    def FileCheck(self):
        """Check if the zip is already extracted."""
        # first, check if folder exists
        zip_path = self.GetPath()
        tmp = zip_path + 'tmp/'
        if os.path.isdir(tmp):
            zipfile = self.GetPath() + self.GetFile()
            zipfile_creation = os.stat(zipfile).st_mtime
            folder_creation = os.stat(tmp).st_mtime
            # Now compare creation dates
            if folder_creation > zipfile_creation:
                # The folder is the most recent element, so we have the last
                # version extracted
                exists = True
            else:
                # The folder is not the most recent element, so we have a
                # newer file to extract.
                exists = False
        else:
            # The folder doesn't exist, so we have to extract the file
            exists = False

        return exists

    def GetDB(self):
        """Extract the DB into a temporally folder."""
        # fist, check if the file alredy exists
        checkfile = self.FileCheck()
        path = self.GetPath()
        tmp_path = self.GetPath() + 'tmp/'
        if checkfile is True:
            files_in_path = os.listdir(tmp_path)
            if len(files_in_path) > 1:
                print(files_in_path)
                raise ValueError('more than one file in dir')
            dbfile = tmp_path + files_in_path[0]
        else:
            zipfile = path + self.GetFile()
            print('origin:', zipfile)
            tmp = self.GetPath() + 'tmp/'
            with ZipFile(zipfile) as zip_file:
                members = zip_file.namelist()
                if len(members) > 1:
                    raise ValueError('more than one entry in the zip file')
                zip_file.extract(members[0], path=tmp)
                print('File found & extracted to tmp folder')
            dbfile = tmp + members[0]
        return dbfile

    def CleanUp(self):
        """Clean de tmp dir after use."""
        tmp_path = self.GetPath() + 'tmp/'
        shutil.rmtree(tmp_path)
        print('tmp folder deleted once used')


class DataYear(object):
    """Group the year data in an object."""

    tdb = TrackDB()
    zipfile = tdb.GetDB()
    db = records.Database('sqlite:///' + zipfile)

    def Year(self):
        """Create an object with all the data of the year."""
        # Elements of the query
        fields = {'work.id': 'id',
                  'project': 'project',
                  'project_name': 'name',
                  'date(started)': 'started',
                  'time(started)': 'hour',
                  'date(stopped)': 'stopped',
                  "strftime('%s',stopped)-strftime('%s', started)": 'lenght'
                  }
        fields_str = ''
        for k in fields:
            r = (k + ' as \'' + fields[k] + '\', ')
            fields_str = fields_str + r
        fields_str = 'SELECT ' + fields_str[0:-2]

        table = ' FROM work'
        constraint = ' WHERE date(started) >= \'2018-01-01\' '
        order = 'ORDER BY datetime(started) ASC'

        # Perform the one-for-all query
        query = fields_str + table + constraint + order

        # The raw query
        df = self.db.query(query)
        print('db hit')  # to measure how many times we hit the db
        self.tdb.CleanUp()
        return df

    def Label(self):
        """Create an object with the labels per id."""
        fields = {'work.id': 'id',
                  'project': 'project',
                  'project_name': 'name',
                  'date(started)': 'started',
                  'time(started)': 'hour',
                  'date(stopped)': 'stopped',
                  "strftime('%s',stopped)-strftime('%s', started)": 'lenght'
                  }
        fields_str = ''
        for k in fields:
            r = (k + ' as \'' + fields[k] + '\', ')
            fields_str = fields_str + r
        fields_str = 'SELECT ' + fields_str[0:-2]

        table = ' FROM work'
        constraint = ' WHERE date(started) >= \'2018-01-01\' '
        order = 'ORDER BY datetime(started) ASC'

        # Perform the one-for-all query
        query = fields_str + table + constraint + order


class Filters(object):
    """Set different filters to apply on queries."""

    def __init__(self):
        """Load all the filters at once."""
        df = DataYear().Year()
        week = self.Week(df)
        # BuildUp
        # bu_year = self.BuProject(df)
        # bu_week = self.BuProject(week)
        bu_year, bu_week = self.BuProject(df), self.BuProject(week)
        # OpK

    def Week(self, data):
        """Get current week's entries."""
        # first, determine last week
        today = date.today()
        delta = timedelta(days=-1)
        start = today
        while start.isocalendar()[2] != 1:  # reduce days until reach monday
            start = start + delta

        # Now, get the entries
        result = []
        for entry in data:
            cur_date = datetime.strptime(entry.started, '%Y-%m-%d').date()
            if cur_date >= start:
                result.append(entry)

        # for row in result:
        #     print(row.id, row.hour, row.name)

        return result

    def BuProject(self, data):
        """Filter bu data (from BU projects only)."""
        prj_id = (19, 20, 21, 22, 23, 24)
        result = []
        for entry in data:
            for id in prj_id:
                if entry.project == id:
                    result.append(entry)

        for row in result:
            print(row.id, row.started, row.hour, row.name)

        return result

# an example
df = Filters()
