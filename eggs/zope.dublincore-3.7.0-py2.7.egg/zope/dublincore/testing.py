##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""Testing support
"""
__docformat__ = 'restructuredtext'

from zope import component

from annotatableadapter import ZDCAnnotatableAdapter
from interfaces import IWriteZopeDublinCore

def setUpDublinCore():
    component.provideAdapter(ZDCAnnotatableAdapter,
                             provides=IWriteZopeDublinCore,
                            )
