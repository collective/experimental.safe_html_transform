##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" CMFActionIcons tool interfaces.

$Id: _tools.py 110650 2010-04-08 15:30:52Z tseaver $
"""

from zope.interface import Interface


class IActionIconsTool(Interface):

    """ Declare product-specific APIs for the CMFActionIcons tools.
    """
