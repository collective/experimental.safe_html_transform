##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

from App.class_init import default__class_init__ as InitializeClass
from Persistence import Persistent
from AccessControl import ClassSecurityInfo
from BTrees.IOBTree import IOBTree
from Utility import _findUserId
import time

MAX32 = int(2**31 - 1)


class EventLog(Persistent):
    """An EventLog encapsulates a collection of log entries."""

    def __init__(self):
        self._data = IOBTree()

    security = ClassSecurityInfo()

    security.declarePrivate('addEntry')
    def addEntry(self, entry):
        """Add a new log entry."""
        if len(self._data):
            key = self._data.minKey() - 1
        else:
            key = MAX32
        self._data[key] = entry

    security.declarePrivate('getEntries')
    def getEntries(self):
        """Return a sequence of log entries."""
        return self._data.values()

    def __len__(self):
        return len(self._data)
    
    def __nonzero__(self):
        return len(self._data) > 0

InitializeClass(EventLog)


class LogEntry(Persistent):
    """A LogEntry contains audit information about a version control
       operation. Actions that cause audit records to be created include 
       checkout and checkin. Log entry information can be read (but
       not changed) by restricted code."""

    # These action constants represent the possible auditable actions.
    ACTION_CHECKOUT = 0
    ACTION_CHECKIN = 1
    ACTION_UNCHECKOUT = 2
    ACTION_UPDATE = 3

    def __init__(self, version_id, action, path=None, message=''):
        self.timestamp = time.time()
        self.version_id = version_id
        self.action = action
        self.message = message
        self.user_id = _findUserId()
        self.path = path

InitializeClass(LogEntry)
