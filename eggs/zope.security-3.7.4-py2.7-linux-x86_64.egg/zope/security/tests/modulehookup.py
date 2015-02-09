##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""Preliminaries to hookup a test suite with the external TestModule.

This is necessary because the test framework interferes with seeing changes in
the running modules via the module namespace.  This enables having some
subject classes, instances, permissions, etc, that don't live in the test
modules, themselves.

$Id: modulehookup.py 95326 2009-01-28 15:11:49Z brandon_rhodes $
"""
from zope.interface import Interface

from zope.security.tests import emptymodule as TestModule

class I(Interface):
    def m1():
        pass
    def m2():
        pass

