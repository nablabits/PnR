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


class Settings(object):
    """Define some useful paths."""

    home = '/home/davif/'
    backup = []
    db_file = home + 'Dropbox/Aplicaciones/Swipetimes Time Tracker/'


class Utils(object):
    """Define some useful algorithms & common functions.

    This object's methods are used by both Week & Year outputs.
    """

    def __init__(self, filters):
        """Init the object."""
        self.filters = filters

    def binary(self, numberlist, number):
        """Perform a number binary search in a given number list.

        Returns a list containing a bool (True if number is found) & a loop
        count.
        """
        numberlist = sorted(numberlist, key=int)
        max, min = numberlist[-1], numberlist[0]
        lenght = len(numberlist) - 1
        lo, hi = 0, lenght  # lo-hi boundaries
        result, loop = False, True
        cur_value = numberlist[-1]
        count = 0

        if number < min:
            # print(number, 'under numberlist')  # DEBUG
            loop = False
        if number > max:
            # print(number, 'over numberlist')  # DEBUG
            loop = False
        if cur_value == number:
            result = True
            loop = False

        while cur_value != number and loop:
            count += 1
            avg_idx = int(floor((lo + hi) / 2))  # get the mid index
            cur_value = numberlist[avg_idx]  # get current value

            if lo >= lenght or hi > lenght:
                # print('not in list')  # DEBUG
                break

            # print('testing', cur_value, number)  # DEBUG

            if cur_value < number:
                lo = avg_idx + 1
                # DEBUG
                # print("[oh, too low]")
                # print(lo, hi, lenght)
                if numberlist[lo] > numberlist[hi]:
                    break
            elif cur_value > number:
                hi = avg_idx - 1
                # print("[oh, too high]")  # DEBUG
                if numberlist[lo] > numberlist[hi]:
                    break
            elif cur_value == number:
                # print('Numbers match!', cur_value, number)  # DEBUG
                result = True
                break

        return (result, count)

    def in_hours(self, number):
        """Convert the given number to hours.

        Returns a rounded float. Input in seconds
        """
        result = round(number / 3600, 2)
        return result

    def SumTimes(self, df):
        """Sum all the lenghts in a data frame.

        Outputs a rounded float.
        """
        # first, check that the data is appropiate.
        check = False
        if isinstance(df, list):
            if isinstance(df, records.Record):
                check = True
        elif isinstance(df, records.Record):
            check = True
        elif not check:
            print(type(df))
            raise ValueError('Can\'t sum this data')

        # DEBUG:
        # for row in df:
        #     print(row.id, row.hour, row.name)

        total = 0
        for row in df:
            if not row.name:
                delta = 0
            if not row.lenght:  # On going processes have no lenght
                start = (row.started + ' ' + row.hour)
                start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                end = datetime.now()
                delta = (end.timestamp() - start.timestamp())
            else:
                delta = row.lenght
            total = total + delta
        total = round(total, 2)
        return total

    def Percents(self, value, total):
        """Calculate the ratio between two numbers.

        Outputs a rounded float. Avoids percents over 100.
        """
        if total < value:
            print(value, total)
            # raise ValueError('Value is higher than total')
        if total == 0:  # avoid division by 0
            result = 0
        else:
            result = round(value * 100 / total, 2)
        return result

    def ProjectTime(self, df, project):
        """Output the hours of a given project in a given time.

        Generic function to be applied to any df & any project. The project
        input could be a tuple a range or a single number.
        Outputs a rounded float (since sum_entries outputs so) or 0 if
        filter has no effect.
        """
        value = 0
        if isinstance(project, tuple) or isinstance(project, range):
            for i in project:
                df_filtered = self.filters.ProjectFilter(df, i)
                # since a non-effect filter returns df again
                if df == df_filtered:
                    addvalue = 0
                else:
                    addvalue = self.in_hours(self.SumTimes(df_filtered))
                # print('adding %s hours from %s' % (addvalue, i))  # DEBUG
                value = addvalue + value
            value = round(value, 2)
        else:
            df_filtered = self.filters.ProjectFilter(df, project)
            # since a non-effect filter returns df again
            if df == df_filtered:
                addvalue = 0
            value = self.in_hours(self.SumTimes(df_filtered))
            # print('adding %s hours from %s' % (value, project))  # DEBUG
        return value

    def AwakeTime(self, df, total_hours):
        """Calculate the awake in a given period.

        Awake time is the base to calculate percents.
        Outputs a list containing: rounded float for the hours
        & percent over total.
        """
        sleep = self.ProjectTime(df, 38)
        value = round(total_hours - sleep, 2)  # discount sleep
        perc = self.Percents(value, total_hours)
        result = (value, perc)
        return result

    def TimeTracked(self, df, sleep):
        """Output the hours of time tracked.

        Returns a rounded float (since SumTimes does so).
        """
        value = self.in_hours(self.SumTimes(df))
        value = round(value - sleep, 2)  # since df includes sleep time
        return value

    def BuTarget(self, bu, awake):
        """Calculate the hours over/under the goal.

        The goal or this year is 20% BuildUp so, this fn lets visualize the
        progress of the goal.
        Returns a string like '+20h over goal'
        """
        goal = 20 * awake / 100
        diff = round(bu - goal, 2)
        if diff > 0:
            output = '+' + str(abs(diff)) + 'h over goal'
        else:
            output = ' ' + str(abs(diff)) + 'h under goal'
        return output

    def Qualitiy(self, df, bu):
        """Output the quality of BuildUp.

        Returns a list containing the percents of quality.
        """
        df_hi = self.filters.LabelFilter(df, '1-hi')
        df_mid = self.filters.LabelFilter(df, '2-mid')
        df_lo = self.filters.LabelFilter(df, '3-lo')

        # DEBUG
        # for item in df_hi:
        #     print(item.id, item.name, item.started)

        if df_hi == df:
            sum_hi = 0
        else:
            sum_hi = self.in_hours(self.SumTimes(df_hi))
        if df_mid == df:
            sum_mid = 0
        else:
            sum_mid = self.in_hours(self.SumTimes(df_mid))
        if df_lo == df:
            sum_lo = 0
        else:
            sum_lo = self.in_hours(self.SumTimes(df_lo))

        # DEBUG
        # print(sum_hi, sum_mid, sum_lo)

        result = (self.Percents(sum_hi, bu),
                  self.Percents(sum_mid, bu),
                  self.Percents(sum_lo, bu))

        return result


class TrackDB(object):
    """Get the last db file & unpack it into a tmp folder."""

    def __init__(self):
        """Init the object."""
        settings = Settings()
        self.db_path = settings.db_file

    def GetPath(self):
        """Select te path to the db file. Try first default.

        Outputs a string with a valid path.
        """
        default = self.db_path
        zip_dir = os.path.isdir(default)
        while zip_dir is False:
            default = input('Couldn\'t find that location, choose manually: ')
            zip_dir = os.path.isdir(default)
        return default

    def GetFile(self):
        """Get the last zip file from the path.

        Outputs a string with the name of the latest file in GetPath.
        """
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
                  'details': 'details',
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
            # print('Filter had no effect (week', start,
            #       ') restoring previous df')
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
            # print('Filter had no effect (day', str(day),
            #       ') restoring previous df')
            result = df
        return result

    def LabelFilter(self, df, label):
        """Filter data with the selected label."""
        # First, get the work ids with selected label
        tags = self.labels
        tag_id_list = []
        utils = Utils(self)

        # Build the tag list
        for entry in tags:
            if entry.tag == label:
                # print(entry.id, entry.tag)
                tag_id_list.append(entry.id)

        # # DEBUG
        # for i in tag_id_list:
        #     print(i)

        # Now compare tag list with data frame using bin search
        result = []
        count = 0
        for entry in df:
            count += 1

            # DEBUG
            # print('testing', entry.id, entry.started, entry.name)

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
            # DEBUG
            # print('Filter had no effect (label', label,
            #       ') restoring previous df')
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
            # print('Filter had no effect (project', project,
            #       ') restoring previous df')
            result = df

        return result


class LastEntries(object):
    """Print last entries for the daily summary."""

    def __init__(self, df, filters, days):
        """Customize the object."""
        self.df = df
        self.filters = filters
        self.days = days
        self.hours = Utils(filters).in_hours

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
        date_list = date_list[::-1]

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
        """Output the result."""
        for i in self.DataFrame():
            print(50 * '*')
            print(i[0].started)
            for row in i:
                hour = row.hour[0:5]
                if not row.lenght:
                    lenght = 'On going'
                else:
                    lenght = str(self.hours(row.lenght)) + 'h'
                name = row.name
                if not row.details:
                    details = 'No comments'
                else:
                    details = row.details
                if not row.name:
                    pass
                else:
                    data = (hour, lenght, name, details)
                    print('%s; (%s) %s: %s' % data)

        return True


class Week(object):
    """Show how it's going the week."""

    def __init__(self, df, filters):
        """Customize the object."""
        self.df = df
        self.filters = filters
        utils = Utils(filters)
        self.hours = utils.in_hours
        self.sum = utils.SumTimes
        self.perc = utils.Percents
        self.p_time = utils.ProjectTime
        self.awake = utils.AwakeTime
        self.tt = utils.TimeTracked
        self.bu_goal = utils.BuTarget
        self.qlty = utils.Qualitiy

        self.Output()

    def TotalHours(self):
        """Calculate the elapsed hours in the week."""
        now = datetime.timestamp(datetime.now())
        today = date.today()
        delta = timedelta(days=-1)
        end = today

        # reduce days until reach last monday
        while end.isocalendar()[2] != 1:
            end = end + delta
        midnight = time(0, 0, 0, 0)
        end = datetime.combine(end, midnight)
        start = datetime.timestamp(end)
        total_hours = (now - start) / 3600
        return total_hours

    def Output(self):
        """Output the data."""
        df = self.df
        awake = self.awake(df, self.TotalHours())

        sleep = self.p_time(df, 38)
        sleep_perc = self.perc(sleep, self.TotalHours())

        tt = self.tt(df, sleep)
        tt_perc = self.perc(tt, awake[0])

        bu_projects = range(19, 25)
        bu = self.p_time(df, bu_projects)
        bu_perc = self.perc(bu, awake[0])
        bu_goal = self.bu_goal(bu, awake[0])

        opk_projects = range(26, 31)
        opk = self.p_time(df, opk_projects)
        opk_perc = self.perc(opk, awake[0])

        qlty = self.qlty(df, bu)

        shared = self.p_time(df, 31)
        shared_perc = self.perc(shared, awake[0])

        output = (sleep_perc, sleep,
                  awake[0],
                  tt_perc, tt,
                  bu_perc, bu, bu_goal,
                  qlty[0], qlty[1], qlty[2],
                  opk_perc, opk,
                  shared_perc, shared,
                  )

        print(50 * '*', '\n' 'Week progress')
        print(' Sleep: %s%% (%sh) \n'
              ' From awake time (%sh): \n'
              '  Time Tracked: %s%% (%sh) \n'
              '  Bu Project time: %s%% (%sh) %s \n'
              '  Bu Qlty: hi, %s%%; mid, %s%%; lo, %s%%  \n'
              '  Opk Project time: %s%% (%sh) \n'
              '  Shared time: %s%% (%sh)'
              % output)


class Menu(object):
    """Display the main menu."""

    def __new__(self):
        """Instantiate the data from db."""
        db = DataYear()
        labels = db.Labels()
        df = db.Year()
        filters = Filters(labels)
        df_week = filters.WeekFilter(df)

        quick = False

        # Quick view
        option = input('Press [y] to perform a quick view (without backup). ')
        if option == 'y':
            LastEntries(df, filters, days=3)
            Week(df_week, filters)

            quick = True

show_menu = Menu()
