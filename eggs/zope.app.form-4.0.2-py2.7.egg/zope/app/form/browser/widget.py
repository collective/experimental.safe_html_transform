##############################################################################
#
# Copyright (c) 2001-2004 Zope Corporation and Contributors.
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
"""Browser Widget Definitions

$Id: widget.py 107818 2010-01-08 19:14:50Z faassen $
"""
__docformat__ = 'restructuredtext'

# BBB
from zope.formlib.widget import (
    quoteattr,
    BrowserWidget,
    SimpleInputWidget,
    DisplayWidget,
    UnicodeDisplayWidget,
    renderTag,
    renderElement,
    escape,
    setUp,
    tearDown)
