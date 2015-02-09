##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Validation Exceptions

$Id: interfaces.py 107371 2009-12-30 18:36:02Z faassen $
"""
__docformat__ = 'restructuredtext'

# this moved to zope.formlib.interfaces
from zope.formlib.interfaces import (IWidgetInputError,
                                     WidgetInputError,
                                     MissingInputError,
                                     ConversionError,
                                     InputErrors,
                                     ErrorContainer,
                                     WidgetsError,
                                     IWidget,
                                     IInputWidget,
                                     IDisplayWidget,
                                     IWidgetFactory)

                          
