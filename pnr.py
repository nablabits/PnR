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
        # to measure how many times we hit the db
        # print('db hit (last entries)')
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
        elif isinstance(period, date):
            period = '\'' + str(period) + '\''
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

    def ProjectDay(self, start, project, day_list):
        """Get the time per project and per day.

        Returns a list of integers. Start must be a datetime.date
        object, while project should be an integer or tuple of integers.
        If a date is not in the list, insert 0 at that position.
        """
        # Check date
        if not isinstance(start, date):
            raise TypeError('Start should be a datetime.date')
        else:
            start = '\'' + str(start) + '\''

        # Check project int
        if not isinstance(project, int):
            if not isinstance(project, tuple):
                raise TypeError('Project should be a list of int or int')
            else:
                project = str(project)
        else:
            project = '(%s)' % project

        field = ("SELECT sum(strftime('%s',stopped)-strftime('%s', started))" +
                 " as lenght, date(started) as date")
        table = ' FROM work'
        constraint = (' WHERE date(started) >= %s ' % start +
                      'AND project IN %s ' % project)
        sorting = 'GROUP BY date(started) ORDER BY date(started) ASC'

        query = field + table + constraint + sorting
        # print('ProjectDay: db hit')
        data = self.db.query(query)

        result = []

        for day in day_list:
            date_in = False
            for row in data:
                if str(day) == row.date:
                    # DEBUG
                    # print('testing %s with %s, found!' % (day, row.date))
                    date_in, lenght = True, row.lenght
            if date_in:
                result.append(lenght)
            else:
                result.append(0)
                # print('date %s not found, adding 0' % day)  # DEBUG

        if not result:
            print('Warning: query (%s, %s) gave no result, is it written ok?'
                  % (project, start))

        # DEBUG
        # for row in result:
        #     print(row)

        return result

    def TagDay(self, start, tag, day_list):
        """Get the time per tag and per day.

        Returns a list of integers. Start must be a datetime.date
        object, while tag should be an str.
        If a date is not in the list, insert 0 at that position.
        """
        # Check date
        if not isinstance(start, date):
            raise TypeError('Start should be a datetime.date')
        else:
            start = '\'' + str(start) + '\''

        # Check tag str
        if not isinstance(tag, str):
            raise TypeError('Tag should be an str')
        else:
            tag = '\'' + tag + '\''

        field = ("SELECT sum(strftime('%s',stopped)-strftime('%s', started))" +
                 " as lenght, date(started) as date")
        table = ' FROM work'
        join1 = ' INNER JOIN work_tag ON work.id=work_id'
        join2 = ' INNER JOIN tag ON tag.id=work_tag.tag_id'
        constraint = (' WHERE date(started) >= %s ' % start +
                      'AND tag.name = %s ' % tag)
        sorting = 'GROUP BY date(started) ORDER BY date(started) ASC'

        query = field + table + join1 + join2 + constraint + sorting
        data = self.db.query(query)
        # print('TagDay: db hit')

        result = []

        for day in day_list:
            date_in = False
            for row in data:
                if str(day) == row.date:
                    # DEBUG
                    # print('testing %s with %s, found!' % (day, row.date))
                    date_in, lenght = True, row.lenght
            if date_in:
                result.append(lenght)
            else:
                result.append(0)
                # print('date %s not found, adding 0' % day)  # DEBUG

        if not result:
            print('Warning: query (%s, %s) gave no result, is it written ok?'
                  % (tag, start))

        # DEBUG
        # for row in result:
        #     print(row)

        return result

    def AwakeDay(self, start, day_list):
        """Get the awake time per day.

        Returns a list of integers. Start must be a datetime.date
        object.
        If a date is not in the list, insert 86400 (24h) at that position.
        """
        # Check date
        if not isinstance(start, date):
            raise TypeError('Start should be a datetime.date')
        else:
            start = '\'' + str(start) + '\''

        field = ("SELECT(86400 - sum(strftime('%s',stopped)-" +
                 "strftime('%s', started))) as lenght, date(started) as date")
        table = ' FROM work'
        constraint = (' WHERE date(started) >= %s ' % start +
                      'AND project = 38 ')
        sorting = 'GROUP BY date(started) ORDER BY date(started) ASC'

        query = field + table + constraint + sorting
        data = self.db.query(query)
        # print('AwakeDay: db hit')

        result = []

        for day in day_list:
            date_in = False
            for row in data:
                if str(day) == row.date:
                    # DEBUG
                    # print('testing %s with %s, found!' % (day, row.date))
                    date_in, lenght = True, row.lenght
            if date_in:
                result.append(lenght)
            else:
                result.append(86400)
                # print('date %s not found, adding 0' % day)  # DEBUG

        # DEBUG
        # for row in data:
        #     print(row)

        return result


class LastEntries(object):
    """Print last entries for the daily summary."""

    def __init__(self):
        """Customize the object."""
        self.days = Settings.last_entries_days
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
        self.tag = db.Tags
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

        period = date(2018, 5, 1)
        bu_may = round(self.tag(period)['BuildUp'])
        py = round(self.tag_times['python'], 2)
        py_perc = round(py * 100 / bu_may)
        web = round(self.tag_times['web'], 2)
        web_perc = round(web * 100 / bu_may)

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
                  py_perc, py, web_perc, web,
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
              '  Python (since may): %s%% (%s); Web: %s%% (%s)\n'
              '  Core Range: %sh %s \n'
              '  Opk Project time: %s%% (%sh) \n'
              '  Opk Ratio (I+D): %s%% \n'
              '  Shared time: %s%% (%sh)'
              % output
              )


class Graph(object):
    """Show powerful graphs to visualize the year progress."""

    def __init__(self):
        """Customize the object."""
        db = DataYear()
        start = Settings.start_graph
        day_list = self.DayList()

        awake_data = db.AwakeDay(start, day_list)

        # BuildUp data
        bu_projects = (19, 20, 21, 22, 23, 24)
        bu_data = db.ProjectDay(start, bu_projects, day_list)
        bu = self.PrepareData(bu_data, awake_data, 'BildUp')

        # BuildUp total data
        bu_tag = 'BuildUp'
        bu_tag_data = db.TagDay(start, bu_tag, day_list)
        bu_total = self.PrepareData(bu_tag_data, awake_data, 'BildUp total')

        # Opk data
        opk_projects = (26, 27, 28, 29, 30)
        opk_data = db.ProjectDay(start, opk_projects, day_list)
        opk = self.PrepareData(opk_data, awake_data, 'Opk')

        shared_projects = (31)
        shared_data = db.ProjectDay(start, shared_projects, day_list)
        shared = self.PrepareData(shared_data, awake_data, 'Shared')

        to_plot = (bu, opk, shared, bu_total)

        TrackDB().CleanUp()  # & Clean the tmp folder.
        if input('Press g to show graph: ') == 'g':
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

    def Aggregation(self, values):
        """Get the acumulated hours per day. Outputs a list of floats."""
        if not isinstance(values, list):
            print(type(values))
            raise TypeError('Aggregation values should be in a list')

        idx = 1
        result = []
        for i in values:
            r = sum(values[0:idx])
            result.append(r)
            idx += 1
        # print(result)
        return result

    def Ratio(self, over, under):
        """Get the ratio between Buildup & awake time per day."""
        if len(over) != len(under):
            print(len(over), len(under))
            raise ValueError('awake & aggregated don\'t match')
        result = []
        for k in over:
            idx = over.index(k)
            # print(idx)
            r = k * 100 / under[idx]
            result.append(r)

        return result

    def PrepareData(self, data, awake_data, label):
        agg = self.Aggregation(data)
        awake_agg = self.Aggregation(awake_data)
        ratio = self.Ratio(agg[:-1], awake_agg[:-1])
        result = {'label': label,
                  'data': ratio}
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
        LastEntries()
        Week()
        Year()
        Graph()

        if input('Press k to backup: ') == 'k':
            Compress()

show_menu = Menu()
