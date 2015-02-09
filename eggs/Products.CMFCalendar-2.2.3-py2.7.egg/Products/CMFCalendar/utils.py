##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Utility functions.

$Id: utils.py 110663 2010-04-08 15:59:45Z tseaver $
"""

from AccessControl import ModuleSecurityInfo
from zope.i18nmessageid import MessageFactory


security = ModuleSecurityInfo('Products.CMFCalendar.utils')

security.declarePublic('Message')
Message = MessageFactory('cmf_calendar')
