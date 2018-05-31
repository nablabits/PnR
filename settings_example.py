"""Define some useful settings."""

from datetime import date


class Settings(object):
    """Define paths several fixed data."""

    # Paths
    home = '/home/user/
    db_file = home + 'Dropbox/Aplicaciones/Swipetimes Time Tracker/'
    backup = ['dir1',
              'dir2/dir3',
              'dir4',
              ]

    # Days to show on last entries summary
    last_entries_days = 3

    # Graph start date
    start_graph = date(2018, 1, 1)
