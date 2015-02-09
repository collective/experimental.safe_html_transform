##############################################################################
#
# Copyright (c) 2005-2009 Zope Foundation and Contributors.
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
"""

$Id: test_namedtemplate.py 111996 2010-05-05 17:34:04Z tseaver $
"""
import os
import os.path
import zope.component.testing
import zope.traversing.adapters


def pageSetUp(test):
    zope.component.testing.setUp(test)
    zope.component.provideAdapter(
        zope.traversing.adapters.DefaultTraversable,
        [None],
        )


def test_suite():
    import doctest
    filename = os.path.join(os.pardir, 'namedtemplate.txt')
    return doctest.DocFileSuite(
        filename,
        setUp=pageSetUp, tearDown=zope.component.testing.tearDown,
        globs={'__file__':  os.path.abspath(os.path.join(os.path.dirname(__file__), filename))}
        )
