##############################################################################
#
# Copyright (c) 2004-2009 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Events in the lifetime of a server process.
"""
from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import implements

class IDatabaseOpened(Interface):
    """The main database has been opened.
    """
    database = Attribute("The main database.")

class DatabaseOpened(object):
    implements(IDatabaseOpened)

    def __init__(self, database):
        self.database = database

class IDatabaseOpenedWithRoot(Interface):
    """The main database has been opened.
    """
    database = Attribute("The main database.")

class DatabaseOpenedWithRoot(object):
    implements(IDatabaseOpenedWithRoot)

    def __init__(self, database):
        self.database = database

class IProcessStarting(Interface):
    """The application server process is starting.
    """

class ProcessStarting(object):
    implements(IProcessStarting)
