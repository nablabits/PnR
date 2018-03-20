"""New comment added"""
import uuid
import tarfile
import os
import re
import shutil
from zipfile import ZipFile
import records
from datetime import date, datetime, timedelta, time


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


class LastEntries:
    """Show last entries for the daily summary."""

    tdb = TrackDB()
    zipfile = tdb.GetDB()
    db = records.Database('sqlite:///' + zipfile)

    delta = timedelta(days=-1)
    today = date.today()
    yesterday = today + delta
    thedaybefore = yesterday + delta

    def BuildQuery(self, day):
        """Build the query respect to the day."""
        day = day.isoformat()
        query = self.db.query("SELECT * FROM work WHERE date(started) =\'" +
                              day + "\' ORDER BY time(started) ASC")
        return query

    def TheDayBeforeEntries(self):
        """Get 2 days ago data."""
        day = self.thedaybefore
        entries = self.BuildQuery(day)
        return entries

    def YesterdayEntries(self):
        """Get yesterday's data."""
        day = self.yesterday
        entries = self.BuildQuery(day)
        return entries

    def TodayEntries(self):
        """Get today's data."""
        day = self.today
        entries = self.BuildQuery(day)
        return entries

    def TimeGap(self, start, end):
        """Calculate the elapsed time of the activity."""
        start = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')

        if not end:
            end = datetime.now()
        else:
            end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
        diff = round((end.timestamp() - start.timestamp()) / 3600, 2)
        return diff

    def BuildOutputStr(self, entry):
        """Build the output string."""
        project = entry.project_name
        if not project:
            project = 'Undefined Project'
        start = entry.started
        end = entry.stopped
        diff = str(self.TimeGap(start, end))
        comments = entry.details
        if not comments:
            comments = 'No comments'
        entry_str = (start + ',(' + diff + 'h) ' + project + ': ' + comments)
        return entry_str

    def OutputToday(self):
        """Finally, output the result."""
        today_entries = self.TodayEntries()
        print('Today:')
        for entry in today_entries:
            entry_str = self.BuildOutputStr(entry)
            print(entry_str)
        print(50 * '*')

    def OutputYesterday(self):
        """Finally, output the result."""
        yesterday_entries = self.YesterdayEntries()
        print('Yesterday:')
        for entry in yesterday_entries:
            entry_str = self.BuildOutputStr(entry)
            print(entry_str)
        print(50 * '*')

    def OutputThedayBefore(self):
        """Finally, output the result."""
        thedaybefore_entries = self.TheDayBeforeEntries()
        print('The day before:')
        for entry in thedaybefore_entries:
            entry_str = self.BuildOutputStr(entry)
            print(entry_str)
        print(50 * '*')


class DataQueriesWeek:
    """Group the year queries in an object."""

    def SelectWeek():
        """Choose the week from where data will be imported (last)."""
        # first, determine last week
        today = date.today()
        delta = timedelta(days=-1)
        start = today

        # reduce days until reach monday
        while start.isocalendar()[2] != 1:
            start = start + delta

        week_range = (start, today)
        return week_range

    tdb = TrackDB()
    zipfile = tdb.GetDB()
    db = records.Database('sqlite:///' + zipfile)
    week_range = SelectWeek()

    if week_range[0] == week_range[1]:
        week_filter = ("date(started) = \'" + str(week_range[0]) + "\'")
    else:
        week_filter = ("date(started) BETWEEN\'" + str(week_range[0]) +
                       "\' AND \'" + str(week_range[1]) + "\'")

    # Tracked time query
    all_times = db.query("SELECT * FROM work WHERE " + week_filter)

    # Sleep time
    sleep_time = db.query("SELECT * FROM work WHERE " + week_filter +
                          " AND project=38")

    # BuildUp Hours this week query
    bu_data = db.query("SELECT * FROM work WHERE " + week_filter +
                       "AND project BETWEEN 19 AND 24")

    # OpK Hours this week query
    opk_data = db.query("SELECT * FROM work WHERE " + week_filter +
                        " AND project BETWEEN 26 AND 30")

    # Quality time {tags 6(mid), 7(hi) & 8(lo)]}
    hi, mid, lo = '7', '6', '8'
    common = ('SELECT started, stopped FROM work ' +
              'INNER JOIN work_tag ON work.id=work_id ' +
              'WHERE work_tag.tag_id = ')
    qlt_hi_data = db.query(common + hi + ' AND ' + week_filter)
    qlt_mid_data = db.query(common + mid + ' AND ' + week_filter)
    qlt_lo_data = db.query(common + lo + ' AND ' + week_filter)


class WeekOutputs:
    """Output the extracted year data."""

    weekqueries = DataQueriesWeek()

    def WeekCurrentHours(self):
        """Calculate the elapsed time since the beginning of the Week."""
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
        sleep = self.SleepTime()
        diff = ((now - start) / 3600) - sleep  # in Hours, discount sleep
        return diff

    def SumTimes(self, df):
        """Sum all the times given by the db query."""
        total = 0
        for row in df:
            start = datetime.strptime(row.started, '%Y-%m-%d %H:%M:%S')
            end = row.stopped
            if not end:
                end = datetime.now()
            else:
                end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')

            diff = (end.timestamp() - start.timestamp()) / 3600  # in hours
            total = round(total + diff, 1)
        return total

    def TimePerc(self, data):
        """Calculate the time tracked %."""
        elapsed = self.WeekCurrentHours()
        result = round(100 * data / elapsed, 1)
        return result

    def QualityPerc(self, data):
        """Qualtiy Percents are calculated over BuildUp Time."""
        bu_time = self.SumTimes(self.weekqueries.bu_data)
        if bu_time == 0:  # Avoid division by 0
            result = 0
        else:
            result = round(100 * data / bu_time, 1)
        return result

    def TimeTracked(self):
        """Calculate the time tracked."""
        df = self.weekqueries.all_times
        sleep = self.SleepTime()
        result = round(self.SumTimes(df) - sleep, 1)
        return result

    def SleepTime(self):
        """Calculate the sleep time."""
        df = self.weekqueries.sleep_time
        result = self.SumTimes(df)
        return result

    def GetString(self, perc, time):
        """Build the string for the output."""
        output = str(perc) + '% (' + str(time) + 'h)'
        return output

    def Output(self):
        """Output all the resuts."""
        # Absolute times
        df = self.weekqueries
        bu = self.SumTimes(df.bu_data)
        bu_hi = self.SumTimes(df.qlt_hi_data)
        bu_mid = self.SumTimes(df.qlt_mid_data)
        bu_lo = self.SumTimes(df.qlt_lo_data)
        opk = self.SumTimes(df.opk_data)
        tt = self.TimeTracked()
        st = self.SleepTime()

        # Percents
        tt_perc = self.TimePerc(tt)
        bu_perc = self.TimePerc(bu)
        bu_hi_perc = self.QualityPerc(bu_hi)
        bu_mid_perc = self.QualityPerc(bu_mid)
        bu_lo_perc = self.QualityPerc(bu_lo)

        # Bu target
        bu_goal = YearOutputs().BuTarget(bu, tt)

        # since current year hours discount the sleep time
        corr = 1 - st / (self.WeekCurrentHours() + st)
        st_perc = round(self.TimePerc(st) * corr, 1)
        opk_perc = self.TimePerc(opk)

        data_str = self.GetString

        output = (('Week progress:'),
                  (' Sleep: ' + data_str(st_perc, st)),
                  (' From Awake time:'),
                  ('  Time Tracked: ' + data_str(tt_perc, tt)),
                  ('  BuildUp: ' + data_str(bu_perc, bu) + bu_goal),
                  ('  Quality: ' +
                   str(bu_hi_perc) + '% hi, ' +
                   str(bu_mid_perc) + '% mid, ' +
                   str(bu_lo_perc) + '% lo'
                   ),
                  ('  OpK: ' + data_str(opk_perc, opk)),)
        return output


class DataQueriesYear:
    """Group the year queries in an object."""

    tdb = TrackDB()
    zipfile = tdb.GetDB()
    db = records.Database('sqlite:///' + zipfile)

    # project dict (unused yet)
    query = db.query("select id, name from project")
    project_dict = {}
    for entry in query:
        add_this = {entry.name: entry.id}
        project_dict.update(add_this)

    # Tracked time query
    all_times = db.query("SELECT * FROM work WHERE started > '2018-01-01'")

    # Sleep time
    sleep_time = db.query("SELECT * FROM work WHERE project=38")

    # BuildUp Hours this year query
    bu_data = db.query("SELECT * FROM work WHERE project " +
                       "BETWEEN 19 AND 24 ORDER BY datetime(started) ASC")

    # OpK Hours this year query & OpK.Tries alone
    opk_data = db.query("SELECT * FROM work WHERE project BETWEEN 26 AND 30")
    opk_tries_data = db.query("SELECT * FROM work WHERE project = 28 ")

    # Quality time {tags 6(mid), 7(hi) & 8(lo)]}
    hi, mid, lo = '7', '6', '8'
    common = ('SELECT work.id, started, stopped FROM work ' +
              'INNER JOIN work_tag ON work.id=work_id ' +
              'WHERE date(started) >= \'2018-01-01\' AND ' +
              'work_tag.tag_id = ')
    qlt_hi_data = db.query(common + hi)
    qlt_mid_data = db.query(common + mid)
    qlt_lo_data = db.query(common + lo)


class YearOutputs:
    """Output the extracted year data."""

    yearqueries = DataQueriesYear()

    def YearCurrentHours(self):
        """Calculate the elapsed time since the beginning of the year."""
        now = datetime.timestamp(datetime.now())
        start = datetime.timestamp(datetime(2018, 1, 1, 0, 0, 0, 0))
        sleep = self.SleepTime()
        diff = ((now - start) / 3600) - sleep  # in Hours, discount sleep
        return diff

    def SumTimes(self, df):
        """Sum all the times given by the db query."""
        total = 0
        for row in df:
            start = datetime.strptime(row.started, '%Y-%m-%d %H:%M:%S')
            end = row.stopped
            if not end:
                end = datetime.now()
            else:
                end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
            diff = (end.timestamp() - start.timestamp()) / 3600  # in hours
            total = round(total + diff, 1)
        return total

    def TimePerc(self, data):
        """Calculate the time tracked %."""
        elapsed = self.YearCurrentHours()
        result = round(100 * data / elapsed, 1)
        return result

    def QualityPerc(self, data):
        """Qualtiy Percents are calculated over BuildUp Time."""
        bu_time = self.SumTimes(self.yearqueries.bu_data)
        result = round(100 * data / bu_time, 1)
        return result

    def OpKPerc(self, data):
        """OpK.Tries Percents are calculated over OpK Time."""
        opk_time = self.SumTimes(self.yearqueries.opk_data)
        result = round(100 * data / opk_time, 1)
        return result

    def BuTarget(self, bu, tt):
        """Calculate the hours over/under the goal."""
        goal = 20 * tt / 100
        diff = round(bu - goal, 2)
        if diff > 0:
            output = '+' + str(abs(diff)) + 'h over goal'
        else:
            output = ' ' + str(abs(diff)) + 'h under goal'
        return output

    def TimeTracked(self):
        """Calculate the time tracked."""
        df = self.yearqueries.all_times
        sleep = self.SleepTime()
        result = round(self.SumTimes(df) - sleep, 1)
        return result

    def SleepTime(self):
        """Calculate the sleep time."""
        df = self.yearqueries.sleep_time
        result = self.SumTimes(df)
        return result

    def NoTagEntries(self):
        """Filter the BuildUp Entries that don't have quality tag."""
        df = self.yearqueries

        # first check if all the BuildUp entries are equal to the sum.
        bu = df.bu_data
        hi = df.qlt_hi_data
        mid = df.qlt_mid_data
        lo = df.qlt_lo_data
        sum_entries = len(bu)
        sum_tags = len(hi) + len(mid) + len(lo)

        count = 0
        if sum_entries != sum_tags:
            print('Found projects without tag. Are the following:')
            for row in bu:
                count += 1
                getid = row.id
                # print('[NEW Loop] · testing bu element:', getid)
                has_tag = False

                # test hi
                if not has_tag:
                    for i in hi:
                        count += 1
                        # print('Hi Testing', getid, 'vs', i.id)
                        if i.id == getid:
                            # print('exit on hi')
                            has_tag = True
                            # print(has_tag)
                            break
                    # else:
                    #     continue
                # print(getid, 'hi tested, continue to mid')

                # test mid
                if not has_tag:
                    for i in mid:
                        count += 1
                        # print('Mid Testing', getid, 'vs', i.id)
                        if i.id == getid:
                            # print(i.id, getid, 'exit on mid')
                            has_tag = True
                            break
                    # print(getid, 'mid tested, continue to lo')

                # test lo
                if not has_tag:
                    for i in lo:
                        count += 1
                        # print('Lo Testing', getid, 'vs', i.id)
                        if i.id == getid:
                            # print(i.id, 'exit on lo')
                            has_tag = True
                            break

                if not has_tag:
                    # print(has_tag)
                    print(row.started, row.project_name)
        else:
            print('No projects without tags, Great!')

        if count != 0:
            print(count, 'loops')

        print(50 * '*')

    def GetString(self, perc, time):
        """Build the string for the output."""
        output = str(perc) + '% (' + str(time) + 'h)'
        return output

    def Output(self):
        """Output all the resuts."""
        # Absolute times
        df = self.yearqueries
        bu = self.SumTimes(df.bu_data)
        bu_hi = self.SumTimes(df.qlt_hi_data)
        bu_mid = self.SumTimes(df.qlt_mid_data)
        bu_lo = self.SumTimes(df.qlt_lo_data)
        opk = self.SumTimes(df.opk_data)
        opk_tries = self.SumTimes(df.opk_tries_data)
        tt = self.TimeTracked()
        st = self.SleepTime()

        # Percents
        tt_perc = self.TimePerc(tt)
        bu_perc = self.TimePerc(bu)
        bu_hi_perc = self.QualityPerc(bu_hi)
        bu_mid_perc = self.QualityPerc(bu_mid)
        bu_lo_perc = self.QualityPerc(bu_lo)
        opk_tries_perc = self.OpKPerc(opk_tries)

        # Bu target
        bu_goal = self.BuTarget(bu, tt)

        # since current year hours discount the sleep time
        corr = 1 - st / (self.YearCurrentHours() + st)
        st_perc = round(self.TimePerc(st) * corr, 1)
        opk_perc = self.TimePerc(opk)

        # Untagged entries
        self.NoTagEntries()

        data_str = self.GetString

        output = (('Year progress:'),
                  (' Sleep: ' + data_str(st_perc, st)),
                  (' From Awake time:'),
                  ('  Time Tracked: ' + data_str(tt_perc, tt)),
                  ('  BuildUp: ' + data_str(bu_perc, bu)) + bu_goal,
                  ('  Quality: ' +
                   str(bu_hi_perc) + '% hi, ' +
                   str(bu_mid_perc) + '% mid, ' +
                   str(bu_lo_perc) + '% lo.'
                   ),
                  ('  OpK: ' + data_str(opk_perc, opk)),
                  ('  OpK ratio: ' + str(opk_tries_perc) + '%'),
                  )
        return output


class Compress(object):
    """Compress and move to the backup folder."""

    def TarFilize(self):
        """Create a backup tarball."""
        print('Tarbal creation start...')

        # Set a random name for the file (.bak for backup)
        get_uuid = uuid.uuid4()
        name = str(get_uuid.int)
        name = name[0:7] + '.bak.tar.gz'

        # Now, create the file
        os.chdir('/home/davif/programak')
        tar = tarfile.open(name, 'w:gz')
        file_list = ('web.info', 'python')

        for i in file_list:
            tar.add(i)
        tar.close
        print('Tarball created ok!')

    def Move(self):
        """Move the backup tarball to the aux device."""
        org = '/home/davif/programak/'
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
            if re.search(r'.bak.tar.gz', line):
                print(line, '-> !file found, moving...')
                start = org + line
                end = dst + line
                shutil.move(start, end)
                print('Moved ok.')

    def save(self):
        """Now, create the backup from its elements."""
        proceed = input('Press any key to create the backup(q to exit)')
        if (proceed != 'q'):
            self.TarFilize()
            self.Move()
            print('Backup successfully completed!')
        else:
            print('Process skipped by user, bye')


class Menu(object):
    """Display a menu to let user skip parts."""

    summary = LastEntries()
    week_df = WeekOutputs()
    year_df = YearOutputs()
    compress = Compress()

    def __init__(self):
        """Selfcreate the object when instantiated."""
        skip = False

        # Quick view
        option = input('Press [y] to perform a quick view. ')
        if option == 'y':
            self.summary.OutputThedayBefore()
            self.summary.OutputYesterday()
            self.summary.OutputToday()
            skip = True

        # Set the lenght of the summary
        loop = True
        while loop is True and skip is False:
            option = input('Number of days for the summary [1-3] [default 1] ')
            if not option:
                option = '1'
            if option == '1':
                self.summary.OutputToday()
                loop = False
            elif option == '2':
                self.summary.OutputYesterday()
                self.summary.OutputToday()
                loop = False
            elif option == '3':
                self.summary.OutputThedayBefore()
                self.summary.OutputYesterday()
                self.summary.OutputToday()
                loop = False
            else:
                print('Try again, please')

        # Now show the progress
        for line in self.week_df.Output():
            print(line)
        print(50 * '*')

        for line in self.year_df.Output():
            print(line)
        print(50 * '*')

        # Clean the tmp folder
        tdb = TrackDB()
        tdb.CleanUp()

        # Finally, launch the backup utility
        if skip is False:
            self.compress.save()

# Finally, start everythig with a sigle call.
show_menu = Menu()
