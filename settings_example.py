"""Define some useful settings."""

from datetime import date


class Settings(object):
    """Define paths several fixed data."""

    # Paths
    home = '/home/user/'
    db_file = home + 'path/to/backup/zip/folder'
    BACKUP_FOLDERS = ['dir1',
                      'dir2/dir3',
                      'dir4',
                      ]
    BACKUP_FILES = ['path/to/file1',
                    'path/to/file2',
                    ]

    BACKUP_TARGET = 'path/to/backup/dir'

    # Days to show on last entries summary
    last_entries_days = 3

    # Graph start date
    start_graph = date(2018, 1, 1)

    # Postgres db settings
    PG_BACKUPDB = True
    PG_USER = 'postgres'
    PG_PASS = 'yourpassword'
    PG_HOST = 'localhost'
    PG_DATABASES = ['db1', 'db2', ]
