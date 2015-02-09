##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Uid Generator.

Provides support for generating unique ids.

$Id: UniqueIdGeneratorTool.py 110665 2010-04-08 16:12:03Z tseaver $
"""

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from BTrees.Length import Length
from OFS.SimpleItem import SimpleItem
from zope.interface import implements

from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import UniqueObject
from Products.CMFUid.interfaces import IUniqueIdGenerator


class UniqueIdGeneratorTool(UniqueObject, SimpleItem):

    """Generator of unique ids.

    This is a dead simple implementation using a counter. May cause
    ConflictErrors under high load and the values are predictable.
    """

    implements(IUniqueIdGenerator)

    id = 'portal_uidgenerator'
    alternative_id = 'portal_standard_uidgenerator'
    meta_type = 'Unique Id Generator Tool'

    security = ClassSecurityInfo()

    security.declarePrivate('__init__')
    def __init__(self):
        """Initialize the generator
        """
        # The previous ``BTrees.Length.Length`` implementation may cause 
        # double unique ids under high load. So for the moment we just use 
        # a simple counter.
        self._uid_counter = 0

    security.declarePrivate('__call__')
    def __call__(self):
        """See IUniqueIdGenerator.
        """
        # For sites that have already used CMF 1.5.1 (and older) the
        # BTrees.Length.Length object has to be migrated to an integer.
        if isinstance(self._uid_counter, Length):
            self._uid_counter = self._uid_counter()
        self._uid_counter += 1
        return self._uid_counter

    security.declarePrivate('convert')
    def convert(self, uid):
        """See IUniqueIdGenerator.
        """
        return int(uid)

InitializeClass(UniqueIdGeneratorTool)
registerToolInterface('portal_uidgenerator', IUniqueIdGenerator)
