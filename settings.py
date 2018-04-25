"""Define some useful settings."""

from datetime import date


class Settings(object):
    # Paths
    home = '/home/davif/'
    db_file = home + 'Dropbox/Aplicaciones/Swipetimes Time Tracker/'
    backup = []

    # Graph start date
    start_graph = date(2018, 1, 1)
