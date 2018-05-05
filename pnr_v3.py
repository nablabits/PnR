"""Provide useful data for final day's summary. V3

Perform a backup of the files as well.
"""
import tarfile
import os
import re
import shutil
from zipfile import ZipFile
import records
from datetime import date, datetime, timedelta, time
from settings import Settings
from matplotlib import pyplot as plt
from math import floor


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

        First checks the data input (should be a list of records.Record, a
        records.Record or a RecordCollection. Then, check if df is None (since
        non effect filters output NoneType).
        Finally, sum all the lenghts and output a rounded float.
        """
        # first, check that the data is appropiate.
        check = False
        if isinstance(df, list):
            for row in df:
                if isinstance(row, records.Record):
                    check = True
                else:
                    print(type(row))
        elif isinstance(df, records.Record):
            check = True
        elif isinstance(df, records.RecordCollection):
            check = True

        if not df:
            # print(type(df))
            pass

        # DEBUG:
        # for row in df:
        #     print(row.id, row.hour, row.name)

        total = 0
        if check is True:
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
                    if delta < 0:
                        print(delta, row.id, row.started, row.hour)
                total = total + delta

        total = round(total, 2)

        return total

    def Percents(self, value, total):
        """Calculate the ratio between two numbers.

        Outputs a rounded float. Avoids percents over 100.
        """
        if total < value:
            # print(value, total)  # DEBUG
            raise ValueError('Value is higher than total')
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
        # input is a list or a range
        if isinstance(project, tuple) or isinstance(project, range):
            for i in project:
                df_filtered = self.filters.ProjectFilter(df, i)
                # since a non-effect filter returns NoneType
                if df_filtered is None:
                    addvalue = 0
                else:
                    addvalue = self.in_hours(self.SumTimes(df_filtered))
                # print('adding %s hours from %s' % (addvalue, i))  # DEBUG
                value = addvalue + value
            value = round(value, 2)
        # input is an int
        else:
            df_filtered = self.filters.ProjectFilter(df, project)
            # since a non-effect filter returns NoneType
            if df_filtered is None:
                addvalue = 0
            value = self.in_hours(self.SumTimes(df_filtered))
            # print('adding %s hours from %s' % (value, project))  # DEBUG
        return value

    def LabelTime(self, df, label):
        """Output the hours of a given label in a given time.

        Generic function to be applied to any df & any label. For the moment
        the label's input should be a string with right one label name.
        Returns a rounded float (since sum_entries outputs so), or 0 if filter
        has no effect.
        """
        value = 0
        df_filtered = self.filters.LabelFilter(df, label)
        # since a non-effect filter returns df again
        if not df_filtered:
            value = 0
        else:
            value = self.in_hours(self.SumTimes(df_filtered))
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
        """Check if the zip is already extracted.

        Returns a bool, true if the file is already extracted.
        """
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
        """Extract the DB into a temporally folder.

        The db (sqlite) is compressed inside a zip file, so extract from there.
        Returns a string with the file name & its full path.
        """
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
        """Clean de tmp dir after use. Returns a confirmation msg."""
        tmp_path = self.GetPath() + 'tmp/'
        shutil.rmtree(tmp_path)
        msg = print('Tmp folder deleted once used')
        return msg


class DataYear(object):
    """Queries for the database."""

    def __init__(self):
        """Start the object."""
        # Pickup the dbfile
        tdb = TrackDB()
        zipfile = tdb.GetDB()
        self.db = records.Database('sqlite:///' + zipfile)

        # Clean the db, deleted entries return weird data
        self.db.query("DELETE FROM work WHERE project <= 1")

    def Year(self):
        """Create an object with all the data of the year.

        Returns a DataFrame (df) with all the entries in the year.
        """
        # Fields of the query
        fields = {'work.id': 'id',
                  'project': 'project',
                  'project_name': 'name',
                  'details': 'details',
                  'date(started)': 'started',
                  'time(started)': 'hour',
                  'date(stopped)': 'stopped',
                  "strftime('%s',stopped)-strftime('%s', started)": 'lenght'
                  }

        # Build the field string
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
        return df

    def Labels(self):
        """Create an object with the labels per id.

        Labels are in a different table, so list them to be applied on
        different filters. Returns a DataFrame (df) with all of them.
        """
        # Fields in the query
        fields = {'work.id': 'id',
                  'tag.name': 'tag'}

        # Build field string.
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
        return df

    """
    *******New Section down here*******
    """

    def LastEntriesQuery(self, day):
        """Create an object with all the data in a given day.

        Returns a DataFrame (df) with all the entries.
        """
        # Fields of the query
        fields = {'work.id': 'id',
                  'project': 'project',
                  'project_name': 'name',
                  'details': 'details',
                  'date(started)': 'started',
                  'time(started)': 'hour',
                  "strftime('%s',stopped)-strftime('%s', started)": 'lenght'
                  }

        # Build the field string
        fields_str = ''
        for k in fields:
            r = (k + ' as \'' + fields[k] + '\', ')
            fields_str = fields_str + r
        fields_str = 'SELECT ' + fields_str[0:-2]

        day = '\'' + str(day) + '\''
        # day = '\'2018-01-01\''

        table = ' FROM work'
        constraint = (' WHERE date(started) = %s ' % day)
        order = 'ORDER BY datetime(started) ASC'

        # Perform the one-for-all query
        query = fields_str + table + constraint + order

        # The raw query
        df = self.db.query(query)
        print('db hit (last entries)')  # to measure how many times we hit the db
        return df

    def Period(self, period):
        """Check if period is valid (and if not, return a valid one)."""
        if period == 'year':
            period = '\'2018-01-01\''
        elif period == 'week':
            today = date.today()
            delta = timedelta(days=-1)
            start = today
            while start.isocalendar()[2] != 1:  # reduce days until reach mon
                start = start + delta
            period = '\'' + str(start) + '\''
        else:
            print('Warning: period (%s) was not' % period +
                  ' understood using default(year)')
            period = '\'2018-01-01\''
        return period

    def Tags(self, period):
        """Create an object that returns sum times per tag and per period.

        Filter entries with python takes a long time, so we filter and sum the
        data from the query itself. Period represents the time filter (week or
        year allowed).
        Returns a dictionary with al the values for each tag.
        """
        # first check if Period is valid
        period = self.Period(period)

        fields = {"sum(strftime('%s',stopped)-" +
                  "strftime('%s', started))": 'lenght',
                  'tag.name': 'tag'}

        # Build the field string for the query
        fields_str = ''
        for k in fields:
            r = (k + ' as \'' + fields[k] + '\', ')
            fields_str = fields_str + r
        fields_str = 'SELECT ' + fields_str[0:-2]

        table = ' FROM work'
        join1 = ' INNER JOIN work_tag ON work.id=work_id'
        join2 = ' INNER JOIN tag ON tag.id=work_tag.tag_id'
        constraint = (' WHERE date(started) >= %s ' % period)
        sorting = 'GROUP BY tag ORDER BY work.id ASC'

        query = fields_str + table + join1 + join2 + constraint + sorting
        result = self.db.query(query)
        # to measure how many times we hit the db # DEBUG
        # print('Tag: db hit, %s period' % period)

        tag_dict = {}
        for row in result:
            # print(row.tag, row.lenght) # DEBUG
            tag_dict[row.tag] = row.lenght / 3600

        return tag_dict

    def Project(self, period):
        # first check if Period is valid
        period = self.Period(period)

        fields = {"sum(strftime('%s',stopped)-" +
                  "strftime('%s', started))": 'lenght',
                  'project_name': 'project'}
        # Build the field string for the query
        fields_str = ''
        for k in fields:
            r = (k + ' as \'' + fields[k] + '\', ')
            fields_str = fields_str + r
        fields_str = 'SELECT ' + fields_str[0:-2]
        table = ' FROM work'
        constraint = (' WHERE date(started) >= %s ' % period)
        sorting = 'GROUP BY project ORDER BY work.id ASC'

        query = fields_str + table + constraint + sorting
        result = self.db.query(query)
        # to measure how many times we hit the db # DEBUG
        # print('Project: db hit, %s period' % period)
        project_dict = {}
        for row in result:
            # print(row.tag, row.lenght) # DEBUG
            project_dict[row.project] = row.lenght / 3600

        return project_dict


class Filters(object):
    """Define useful filters for the data extracted from db.

    Filters return always a list of records.
    """

    def __init__(self, labels):
        """Create the object. Labels are needed to build the label filter."""
        self.labels = labels

    def DfType(self, df, filter):
        """Check the df as input or output.

        Raise an error if input/output data have errors. Allowed types are:
        records.RecordCollection or a list containing records.Record entries.
        Filter is used to trace where are the errors.
        Now, since filters can output None type, they are allowed.
        """
        result = None
        # print('DFType Test')
        if isinstance(df, list):
            error = False
            for row in df:
                if not isinstance(row, records.Record):
                    error = True
            if error:
                raise ValueError('The list of %s contains mixed data' % filter)
            # result = print('list', filter)  # DEBUG

        elif isinstance(df, records.RecordCollection):
            pass
            # result = print('Records collection', filter)  # DEBUG

        elif not df:
            pass
            # print(type(df), filter)  # DEBUG

        else:
            result = print(type(df), filter)

        # print('DFType test end', result)
        return result

    def WeekFilter(self, df):
        """Filter current week's entries.

        This filter checks the current week and filters the entries that match
        that date. Returns a list of records.Record.
        """
        # First check the df
        self.DfType(df, filter='(Week Filter, input)')

        # Now, determine last week
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

        # Warning if filter has no effect
        if not result:
            # DEBUG
            # print('Filter had no effect (week', start,
            #       ') Output None')
            result = None

        # Check output
        self.DfType(result, filter='(Week Filter, output)')

        return result

    def DayFilter(self, df, day):
        """Filter entries in a given day.

        This function filters the entries started in the current day. Returns a
        list of records.Record
        """
        # First check the df
        self.DfType(df, filter='(Day Filter, input)')

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
            # DEBUG
            # print('Filter had no effect (day', str(day),
            #       ') Output None')
            result = None

        # Check output
        self.DfType(result, filter='(Day Filter, output)')

        return result

    def LabelFilter(self, df, label):
        """Filter data with the selected label.

        This function filters the entries which match with the given label
        using a binary search. Outputs a list of records.Record.
        """
        # first check the df
        self.DfType(df, filter='(Label Filter, input)')

        # Get the work ids with selected label
        tags = self.labels
        tag_id_list = []
        utils = Utils(self)

        # Build the tag list
        for entry in tags:
            if entry.tag == label:
                # print(entry.id, entry.tag)  # DEBUG
                tag_id_list.append(entry.id)

        # DEBUG
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

        # DEBUG print result
        # for row in result:
        #     print(row.id, row.started, row.hour, row.name)
        # print('in', count, 'loops')

        # Warning if filter have no effect
        if not result:
            # DEBUG
            # print('Filter had no effect (label', label,
            #       ') Output NoneType')
            result = None

        # Check type of df DEBUG
        self.DfType(result, filter='(Label Filter, output)')

        return result

    def ProjectFilter(self, df, project):
        """Filter by project.

        This function filters the df which match with a given project. Project
        input should be an int. Returns a list of records.Record or NoneType if
        filter didn't work.
        """
        self.DfType(df, filter='(Project Filter)')  # Check type of df DEBUG

        result = []
        for entry in df:
            if entry.project == project:
                result.append(entry)

        # DEBUG:
        # for row in result:
        #     print(row.id, row.hour, row.name, row.project)

        # Warning if filter have no effect
        if not result:
            # DEBUG: print warning
            # print('Filter had no effect (project', project,
            #       ') Output NoneType')
            result = None

        # Check type of df DEBUG
        self.DfType(result, filter='(Project Filter, output)')

        return result

    def StartFilter(self, df, start):
        """Filter entries from a start date.

        This function filters the data from the start date up to today.
        """
        # First check the df
        self.DfType(df, filter='(Day Filter, input)')

        if not isinstance(start, date):
            raise TypeError('Date not recognized')

        result = []
        for entry in df:
            curr_date = datetime.strptime(entry.started, '%Y-%m-%d').date()
            if curr_date >= start:
                result.append(entry)

        # DEBUG: results of the filter
        # for row in result:
        #     print(row.id, row.started, row.name)

        if not result:
            # DEBUG
            print('Filter had no effect (day', str(start),
                  ') Output NoneType')
            result = None

        # Check output
        self.DfType(result, filter='(Day Filter, output)')

        return result


class LastEntries(object):
    """Print last entries for the daily summary."""

    def __init__(self, days):
        """Customize the object."""
        self.days = days

        # return the entries
        self.Output()

    def DateList(self):
        """Create a list with the dates to be shown.

        Returns a list of date.datetime objects.
        """
        add_day = date.today()
        delta = timedelta(days=-1)
        date_list = []
        for i in range(0, self.days):
            date_list.append(add_day)
            add_day = add_day + delta
        date_list = date_list[::-1]

        # DEBUG: dates list
        # print(date_list)

        return date_list

    def DataFrame(self):
        """Create a list with the data to be shown.

        Returns a list that contains n lists (one per day) each one with a
        records.Record, since filters always output a list.
        """
        db = DataYear()
        last_entries = db.LastEntriesQuery
        date_list = self.DateList()
        df = []

        for i in date_list:
            data_filtered = last_entries(i)
            df.append(data_filtered)

        return df

    def Output(self):
        """Output the result.

        Take each one of the days in the df and print the entries. The input is
        list with n lists (one per day) each one with a records.Record.
        """
        df = self.DataFrame()
        day = 0
        for entry in df:
            print(50 * '*')
            print(self.DateList()[day])
            day += 1
            for row in entry:
                hour = row.hour[0:5]
                if not row.lenght:
                    lenght = 'On going'
                else:
                    lenght = str(round(row.lenght / 3600, 2)) + 'h'
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
    def __init__(self):
        db = DataYear()
        self.tag_times = db.Tags(period='week')
        self.project_times = db.Project(period='week')

        self.Output()

    def TotalHours(self):
        """Calculate the elapsed hours in the week.

        Outputs a rounded float with the hours elapsed since monday @0:00.
        """
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
        total_hours = round((now - start) / 3600, 2)
        return total_hours

    def TestKeys(self, test_type, keyname):
        """Test the keys to avoid KeyError.

        Since some projects in the week could not have no key yet, test it and
        return 0 in case. Otherwise, return the value for the key.
        """
        if test_type == 'project':
            try:
                value = self.project_times[keyname]
            except KeyError:
                # print('Key (%s) not found adding 0' % keyname)  # DEBUG
                value = 0
        elif test_type == 'tag':
            try:
                value = self.tag_times[keyname]
                # break
            except KeyError:
                # print('Key (%s) not found adding 0' % keyname)  # DEBUG
                value = 0
        else:
            raise ValueError('type unknown')
        return value

    def Output(self):
        """Output the data.

        Using the commom functions, output quantities and percents.
        """
        week = date.isocalendar(date.today())[1]
        total_hours = self.TotalHours()
        test = self.TestKeys
        test_type = ('project', 'tag')

        sleep = round(test(test_type[0], 'Shift.Sleep'), 2)
        sleep_perc = round(sleep * 100 / total_hours, 2)

        awake = round(total_hours - sleep, 2)

        tt = 0 - sleep
        for k in self.project_times:
            tt = tt + self.project_times[k]
        tt = round(tt, 2)
        tt_perc = round(tt * 100 / awake, 2)

        bu = round(test(test_type[0], 'BuildUp.CS') +
                   test(test_type[0], 'BuildUp.Math') +
                   test(test_type[0], 'BuildUp.FR') +
                   test(test_type[0], 'BuildUp.DE') +
                   test(test_type[0], 'BuildUp.Jap') +
                   test(test_type[0], 'BuildUp.Others'), 2
                   )
        bu_perc = round(bu * 100 / awake, 2)

        bu_hi = round(test(test_type[1], '1-hi') * 100 / bu)
        bu_mid = round(test(test_type[1], '2-mid') * 100 / bu)
        bu_lo = round(test(test_type[1], '3-lo') * 100 / bu)

        opk = round(test(test_type[0], 'OpK.Urgoiti.2018') +
                    test(test_type[0], 'OpK.GoBasquing.2018') +
                    test(test_type[0], 'OpK.Tourne.2018') +
                    test(test_type[0], 'OpK.Others.2018') +
                    test(test_type[0], 'OpK.Tries.2018'), 2
                    )
        opk_perc = round(opk * 100 / awake, 2)

        shared = round(test(test_type[0], 'StuffBox.Shared'), 2)
        shared_perc = round(shared * 100 / awake, 2)

        output = (sleep_perc, sleep,
                  awake,
                  tt_perc, tt,
                  bu_perc, bu,
                  bu_hi, bu_mid, bu_lo,
                  opk_perc, opk,
                  shared_perc, shared,
                  )
        print(50 * '*', '\n Week #%s progress (v3)' % week)
        print(' Sleep: %s%% (%sh) \n'
              ' From awake time (%sh): \n'
              '  Time Tracked: %s%% (%sh) \n'
              '  Bu Project time: %s%% (%sh) \n'
              '  Bu Qlty: hi, %s%%; mid, %s%%; lo, %s%%  \n'
              '  Opk Project time: %s%% (%sh) \n'
              '  Shared time: %s%% (%sh)'
              % output)


class Year(object):
    """Refactor current year by filtering right from the db."""

    def __init__(self):
        db = DataYear()
        self.tag_times = db.Tags(period='year')
        self.project_times = db.Project(period='year')
        self.Output()

    def TotalHours(self):
        """Calculate the elapsed hours in the Year.

        Outputs a rounded float with the hours elapsed since Jan 1 00:00.
        """
        now = datetime.timestamp(datetime.now())
        start = datetime(2018, 1, 1, 0, 0, 0, 0)
        start = datetime.timestamp(start)
        total_hours = round((now - start) / 3600, 2)
        return total_hours

    def Output(self):
        """Output the data.

        Using the commom functions, output quantities and percents.
        """

        print(50 * '*', '\n' 'Year progress (V3)')
        total_hours = self.TotalHours()
        sleep = round(self.project_times['Shift.Sleep'])
        sleep_perc = round(sleep * 100 / total_hours, 2)

        awake = round(total_hours - sleep, 2)

        tt = 0 - sleep
        for k in self.project_times:
            tt = tt + self.project_times[k]
        tt = round(tt, 2)
        tt_perc = round(tt * 100 / awake, 2)

        bu = round(self.project_times['BuildUp.CS'] +
                   self.project_times['BuildUp.Math'] +
                   self.project_times['BuildUp.FR'] +
                   self.project_times['BuildUp.DE'] +
                   self.project_times['BuildUp.Jap'] +
                   self.project_times['BuildUp.Others'], 2
                   )
        bu_perc = round(bu * 100 / awake, 2)

        bu_hi = round(self.tag_times['1-hi'] * 100 / bu)
        bu_mid = round(self.tag_times['2-mid'] * 100 / bu)
        bu_lo = round(self.tag_times['3-lo'] * 100 / bu)

        bu_total = round(self.tag_times['BuildUp'], 2)
        bu_total_perc = round(bu_total * 100 / awake, 2)
        bu_goal = round(bu_total - (awake * 0.2), 2)
        if bu_goal >= 0:
            bu_goal = ('%sh over goal' % bu_goal)
        else:
            bu_goal = ('%sh under goal' % abs(bu_goal))

        core = round(self.tag_times['Core'], 2)
        week = date.today().isocalendar()[1]
        corerange = (week * 18, week * 20)

        opk_tries = self.project_times['OpK.Tries.2018']
        opk = round(self.project_times['OpK.Urgoiti.2018'] +
                    self.project_times['OpK.GoBasquing.2018'] +
                    self.project_times['OpK.Tourne.2018'] +
                    self.project_times['OpK.Others.2018'] +
                    opk_tries, 2
                    )
        opk_perc = round(opk * 100 / awake, 2)
        opk_ratio = round(opk_tries * 100 / opk, 2)

        shared = round(self.project_times['StuffBox.Shared'], 2)
        shared_perc = round(shared * 100 / awake, 2)

        output = (sleep_perc, sleep,
                  awake,
                  tt_perc, tt,
                  bu_perc, bu,
                  bu_hi, bu_mid, bu_lo,
                  bu_total_perc, bu_total, bu_goal,
                  core, corerange,
                  opk_perc, opk,
                  opk_ratio,
                  shared_perc, shared,
                  )

        print(' Sleep: %s%% (%sh) \n'
              ' From awake time (%sh): \n'
              '  Time Tracked: %s%% (%sh) \n'
              '  Bu Project time: %s%% (%sh) \n'
              '  Bu Qlty: hi, %s%%; mid, %s%%; lo, %s%%  \n'
              '  BuildUp Total: %s%% (%sh) %s \n'
              '  Core Range: %sh %s \n'
              '  Opk Project time: %s%% (%sh) \n'
              '  Opk Ratio (I+D): %s%% \n'
              '  Shared time: %s%% (%sh)'
              % output
              )


class Graph(object):
    """Show powerful graphs to visualize the year progress."""

    def __init__(self, df, filters):
        """Customize the object."""
        self.df = df
        self.filters = filters
        bu_ids = range(19, 25)
        bu = self.PrepareData(df, bu_ids, label='BuildUp')

        opk_ids = range(26, 31)
        opk = self.PrepareData(df, opk_ids, label='OpK')

        shared_id = (31, )
        shared = self.PrepareData(df, shared_id, label='Shared')

        bu_tag_id = ('BuildUp',)
        bu_tag = self.PrepareData(df, bu_tag_id, label='Bu Total')

        to_plot = (bu, opk, shared, bu_tag)
        self.PlotIt(to_plot)

    def DayList(self):
        """Create a list with all the dates since 20-01-2018.

        The df used for the graph starts on jan 20 so dates must start then.
        Outputs a list of datetime.date objects.
        """
        start = Settings.start_graph
        end = date.today()
        delta = timedelta(days=1)
        result = []
        while start <= end:
            result.append(start)
            start = start + delta
        return result

    def PerDay(self, day_list, data):
        """List of elapsed time in the activity per day (& could be 0).

        Outputs a list of float values.
        """
        result = []
        count = 0
        for day in day_list:
            count += 1
            have_entry = False
            lenght = 0
            for entry in data:
                # print(day, entry.day, entry.lenght)

                if entry.started == str(day):
                    count += 1
                    have_entry = True
                    if not entry.lenght:
                        lenght = lenght + 0
                    else:
                        lenght = lenght + entry.lenght
                    # DEBUG: print info
                    # print(day, entry.started, entry.lenght, entry.name,
                    #       lenght)

            if have_entry is False:
                result.append(0)
                # print(day, 0)  # DEBUG
            else:
                result.append(lenght)
        # print(count, 'loops')  # DEBUG
        result = [float(i) for i in result]  # convert all items into floats

        # DEBUG: print list
        # for i in result:
        #     print(i)

        return result

    def Aggregation(self, values):
        """Get the acumulated hours per day. Outputs a list of floats."""
        idx = 1
        result = []
        for i in values:
            r = sum(values[0:idx])
            result.append(r)
            idx += 1
        # print(result)
        return result

    def AwakeData(self, df):
        """Get a list of awake hours.

        Awake time is used for calculate the ratio of activities, so it must be
        calculated once.
        """
        sleep = self.filters.ProjectFilter(df, 38)
        day_list = self.DayList()
        sleep_per_day = self.PerDay(day_list, sleep)
        awake_per_day = [(86400 - i) for i in sleep_per_day]  # In seconds
        agg_awake = self.Aggregation(awake_per_day)
        return agg_awake

    def PrepareData(self, df, label_id, label):
        """Transform the original dataframe into a valid data for graph.

        Df is a list of record.Records, they must be transformed into a list of
        values per day (amount of hours) so graph can understand it. First
        we'll filter the data to match project (int) or the tag (str), then,
        we'll get the time per day & the aggregated data as a list of floats.

        Finally, create a dic
        with the label & the data.
        """
        # Label id should be a list
        if not isinstance(df, list):
            raise TypeError('Label id should be a list.')

        # Filter the data
        df_filtered = []
        for id in label_id:
            # print('(1041) filtering graph', id)  # DEBUG
            if isinstance(id, int):
                filtered = self.filters.ProjectFilter(df, id)
                if filtered != df:
                    df_filtered.append(filtered)
                else:
                    # DEBUG: print warning
                    # print('(1046)filter returned the same data, none append')
                    pass
            elif isinstance(id, str):
                filtered = self.filters.LabelFilter(df, id)
                if filtered != df:
                    df_filtered.append(filtered)
                else:
                    # DEBUG: print warning
                    # print('(1046)filter returned the same data, none append')
                    pass

        # Combine into a single tuple so PerDay() can understand
        combined = []
        for element in df_filtered:
            if isinstance(element, list) or isinstance(element, tuple):
                for item in element:
                    combined.append(item)
            else:
                combined.append(element)

        # Get the data per day
        # print('(1059) calculate data per day') # DEBUG
        day_list = self.DayList()
        data_per_day = self.PerDay(day_list, combined)

        # Get the ratio between awake and the activity
        awake = self.AwakeData(df)

        # And the acumulated data
        aggregated = self.Aggregation(data_per_day)

        # awake & aggregated must match
        if len(awake) != len(aggregated):
            raise ValueError('awake & aggregated don\'t match')

        data = []
        for k in aggregated:
            idx = aggregated.index(k)
            # print(k, awake[idx])  # DEBUG
            r = k * 100 / awake[idx]
            data.append(r)

        # Finally, create the dict and return it.
        result = {'label': label,
                  'data': data}
        return result

    def PlotIt(self, data):
        """Output the plot.

        Transforms every item in data (list of floats) into a line in the plot
        and adds the label.
        """
        # Graph features
        plt.axhline(y=20, linewidth='2')
        plt.ylabel('% over time tracked')
        plt.grid(color='lime', linestyle='-', linewidth='0.5')

        # fill-in data
        for row in data:
            data = row['data']  # y-axis values
            # print(len(data))  # DEBUG:
            xvalues = [day for day in range(0, len(data))]  # x-axis values
            last = -(len(xvalues) - 20)  # first days are quite irregular
            plt.plot(xvalues[last:], data[last:], label=row['label'])

        # Finally, show the graph
        plt.legend()
        plt.show()


class Compress(object):
    """Compress and move to the backup folder."""

    def __init__(self):
        """Create the backup from its elements."""
        proceed = input('Press any key to create the backup(q to exit)')
        if (proceed != 'q'):
            self.TarFilize()
            self.Move()
            print('Backup successfully completed!')
        else:
            print('Process skipped by user, bye')

    def TarFilize(self):
        """Create a backup tarball."""
        print('Tarbal creation start...')

        now = datetime.now()
        name = (str(now.date()) + '-' + str(now.hour) + str(now.minute) +
                '.tar.gz')

        # Now, create the file
        os.chdir(Settings.home)
        tar = tarfile.open(name, 'w:gz')
        file_list = (Settings.backup)

        for i in file_list:
            checkfile = os.path.isdir(i)
            if checkfile is True:
                tar.add(i)
        tar.close
        input('Tarball created ok!, insert an usb stick & hit any key')

    def Move(self):
        """Move the backup tarball to the aux device."""
        org = Settings.home
        dst = '/media/davif/backup/'  # USB stick should mount auto here

        checkdir = os.path.isdir(dst)
        while not checkdir:
            dst = input('Couldn\'t find that location, ' +
                        'choose manually [q, quit]: ')
            if dst == 'q':
                raise KeyboardInterrupt('Process interrupted by user')

            checkdir = os.path.isdir(dst)

        # Look for all the backup tarballs (.bak.tar.gz) in the dir & move'em
        for line in os.listdir(org):
            if re.search(r'.tar.gz', line):
                print(line, '-> !file found, moving...')
                start = org + line
                end = dst + line
                shutil.move(start, end)
                print('Moved ok.')


class Menu(object):
    """Display the main menu."""

    def __new__(self):
        """Instantiate the data from db."""
        LastEntries(5)
        Week()
        Year()
        # Graph(df_graph, filters)

        # if option != 'y':
        #     Compress()

        TrackDB().CleanUp()  # & Clean the tmp folder.

show_menu = Menu()
