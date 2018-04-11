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
from math import floor


class Utils(object):
    """Define some useful algorithms."""

    def binary(self, numberlist, number):
        """Perform a number binary search in a given number list."""
        max, min = numberlist[-1], numberlist[0]
        lenght = len(numberlist) - 1
        lo, hi = 0, lenght  # lo-hi boundaries
        result, loop = False, True
        cur_value = numberlist[-1]
        count = 0

        if number < min:
            # DEBUG
            # print(number, 'under numberlist')
            loop = False
        if number > max:
            # DEBUG
            # print(number, 'over numberlist')
            loop = False

        while cur_value != number and loop:
            count += 1
            avg_idx = int(floor((lo + hi) / 2))  # get the mid index
            cur_value = numberlist[avg_idx]  # get current value

            if lo >= lenght or hi > lenght:
                # DEBUG
                # print('not in list')
                break

            # DEBUG
            # print('testing', cur_value, number)
            if cur_value < number:
                lo = avg_idx + 1
                # DEBUG
                # print("[oh, too low]")
                # print(lo, hi, lenght)
                if numberlist[lo] > numberlist[hi]:
                    break
            elif cur_value > number:
                hi = avg_idx - 1
                # DEBUG
                # print("[oh, too high]")
                if numberlist[lo] > numberlist[hi]:
                    break
            elif cur_value == number:
                # DEBUG
                # print('Numbers match!', cur_value, number)
                result = True
                break

        return (result, count)


class TrackDB(object):
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
                # DEBUG
                # print(files_in_path)
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

    def __init__(self):
        """Start the object."""
        # Pickup the dbfile
        tdb = TrackDB()
        zipfile = tdb.GetDB()
        self.db = records.Database('sqlite:///' + zipfile)
        tdb.CleanUp()

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
        # self.tdb.CleanUp()
        return df

    def Labels(self):
        """Create an object with the labels per id."""
        fields = {'work.id': 'id',
                  'tag.name': 'tag'}
        fields_str = ''
        for k in fields:
            r = (k + ' as \'' + fields[k] + '\', ')
            fields_str = fields_str + r
        fields_str = 'SELECT ' + fields_str[0:-2]

        table = ' FROM work'
        join1 = ' INNER JOIN work_tag ON work.id=work_id'
        join2 = ' INNER JOIN tag ON tag.id=work_tag.tag_id'
        constraint = ' WHERE date(started) >= \'2018-01-01\''
        order = ' ORDER BY work.id ASC'

        # Perform the one-for-all query
        query = fields_str + table + join1 + join2 + constraint + order

        df = self.db.query(query)
        print('db hit (labels)')  # to measure how many times we hit the db
        # self.tdb.CleanUp()
        return df


class Filters(object):
    """Define useful filters for the data extracted form db."""

    def __init__(self, labels):
        """Create the object."""
        self.labels = labels

    def WeekFilter(self, df):
        """Filter current week's entries."""
        # first, determine last week
        today = date.today()
        delta = timedelta(days=-1)
        start = today
        while start.isocalendar()[2] != 1:  # reduce days until reach monday
            start = start + delta

        # Now, get the entries
        result = []
        for entry in df:
            cur_date = datetime.strptime(entry.started, '%Y-%m-%d').date()
            if cur_date >= start:
                result.append(entry)

        # DEBUG:
        # for row in result:
        #     print(row.id, row.hour, row.name)

        # Warning if filter have no effect
        if not result:
            print('Filter had no effect (week', start,
                  ') restoring previous df')
            result = df

        return result

    def DayFilter(self, df, day):
        """Filter entries in a given day."""
        if not isinstance(day, date):
            raise TypeError('Date not recognized')
        result = []
        for entry in df:
            curr_date = datetime.strptime(entry.started, '%Y-%m-%d').date()
            if curr_date == day:
                result.append(entry)

        # DEBUG: results of the filter
        # for row in result:
        #     print(row.id, row.started, row.name)

        if not result:
            print('Filter had no effect (day', str(day),
                  ') restoring previous df')
            result = df
        return result

    def LabelFilter(self, df, label):
        """Filter data with the selected label."""
        # First, get the work ids with selected label
        tags = self.labels
        tag_id_list = []
        utils = Utils()

        # Build the tag list
        for entry in tags:
            if entry.tag == label:
                # print(entry.id, entry.tag)
                tag_id_list.append(entry.id)

        # DEBUG
        # for i in tag_id_list:
        #     print(i)

        # Now compare tag list with data frame using bin search
        result = []
        count = 0
        for entry in df:
            count += 1
            # print('testing', entry.id)
            binary = utils.binary(tag_id_list, entry.id)
            if binary[0] is True:
                # print('adding', entry.id)
                result.append(entry)
                count = count + binary[1]

        # DEBUG larger loop
        # this is 116 times larger
        # for entry in df:
        #     count += 1
        #     for tag in tag_id_list:
        #         count += 1
        #         if entry.id == tag:
        #             result.append(entry)

        # DEBUG print result
        # for row in result:
        #     print(row.id, row.started, row.hour, row.name)
        # print('in', count, 'loops')

        # Warning if filter have no effect
        if not result:
            print('Filter had no effect (label', label,
                  ') restoring previous df')
            result = df

        return result

    def ProjectFilter(self, df, project):
        """Filter by project."""
        result = []
        for entry in df:
            if entry.project == project:
                result.append(entry)

        # DEBUG:
        # for row in result:
        #     print(row.id, row.hour, row.name, row.project)

        # Warning if filter have no effect
        if not result:
            print('Filter had no effect (project', project,
                  ') restoring previous df')
            result = df

        return result


class LastEntries(object):
    """Print last entries for the daily summary."""

    def __init__(self, df, filters, days):
        self.df = df
        self.filters = filters
        self.days = days

        self.Output()

    def DateList(self):
        """Create a list with the dates to be shown."""
        add_day = date.today()
        delta = timedelta(days=-1)
        days = self.days
        date_list = []
        for i in range(0, days):
            date_list.append(add_day)
            add_day = add_day + delta

        # DEBUG: dates list
        # print(date_list)

        return date_list

    def DataFrame(self):
        """Create a list with the data to be shown."""
        date_list = self.DateList()
        data_frame = []
        
        for i in date_list:
            data_filtered = self.filters.DayFilter(self.df, i)
            data_frame.append(data_filtered)

        return data_frame

    def Output(self):
        """Outputs the result."""
        pass
        # for i in range(0, days):


class Menu(object):
    """Display the main menu."""

    def __new__(self):
        """Instantiate the data from db."""
        db = DataYear()
        labels = db.Labels()
        df = db.Year()
        filters = Filters(labels)

        quick = False

        # Quick view
        option = input('Press [y] to perform a quick view (without backup). ')
        if option == 'y':
            output = LastEntries(df, filters, days=3)
            quick = True

# show_menu = Menu()
