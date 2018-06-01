"""Define some useful settings."""

from datetime import date


class Settings(object):
    """Define paths several fixed data."""

    # Paths
<<<<<<< HEAD
    home = '/home/user/'
=======
    home = '/home/user/
>>>>>>> 90995e3386e7b777f0048dbf675c9089e0c12558
    db_file = home + 'path/to/backup/zip/folder'
    backup = ['dir1',
              'dir2/dir3',
              'dir4',
              ]

    # Days to show on last entries summary
    last_entries_days = 3

    # Graph start date
    start_graph = date(2018, 1, 1)
