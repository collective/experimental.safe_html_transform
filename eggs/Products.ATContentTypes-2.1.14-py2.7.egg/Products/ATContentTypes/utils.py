import datetime
from DateTime import DateTime


def dt2DT(date):
    """Convert Python's datetime to Zope's DateTime
    """
    return DateTime(date)


def DT2dt(date):
    """Convert Zope's DateTime to Pythons's datetime
    """
    return date.asdatetime()


def toTime(date):
    """get time part of a date
    """
    if isinstance(date, datetime.datetime):
        date = DateTime(date)
    return date.Time()


def toSeconds(td):
    """Converts a timedelta to an integer representing the number of seconds
    """
    return td.seconds + td.days * 86400
