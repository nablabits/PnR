"""Define some useful settings."""

from datetime import date


class Settings(object):
    """Define paths several fixed data."""

    # Paths
    home = '/home/davif/'
    db_file = home + 'Dropbox/Aplicaciones/Swipetimes Time Tracker/'
    backup = ['git',
              'programs/python',
              'dev',
              ]

    # Graph start date
    start_graph = date(2018, 1, 1)
