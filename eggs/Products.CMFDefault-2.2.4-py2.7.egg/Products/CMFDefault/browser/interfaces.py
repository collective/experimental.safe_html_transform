##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Browser view interfaces. """

from zope.interface import Interface
from zope.schema import Bool
from zope.schema import Choice
from zope.schema import Int
from zope.schema import TextLine


class IFolderItem(Interface):
    """Schema for folderish objects contents."""
    
    select = Bool(
        required=False)
        
    name = TextLine(
        title=u"Name",
        required=False,
        readonly=True)


class IDeltaItem(Interface):
    """Schema for delta"""    
    delta = Choice(
        title=u"By",
        description=u"Move an object up or down the chosen number of places.",
        required=False,
        vocabulary=u'cmf.contents delta vocabulary',
        default=1)

        
class IHidden(Interface):
    """Schema for hidden items"""
    
    b_start = Int(
        title=u"Batch start",
        required=False,
        default=0)
        
    sort_key = TextLine(
        title=u"Sort key",
        required=False)
        
    reverse = Int(
        title=u"Reverse sort order",
        required=False)
