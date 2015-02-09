##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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
"""Physical Location Adapter Tests
"""
from unittest import TestCase, main, makeSuite

from zope.container.contained import contained
from zope.interface import implements
from zope.location.interfaces import ILocationInfo, IRoot
from zope.site.site import LocalSiteManager
from zope.site.site import SiteManagerContainer
from zope.testing.cleanup import CleanUp

import zope.traversing.testing


class Root(object):
    implements(IRoot)

    __parent__ = None


class C(object):
    pass


class Test(CleanUp, TestCase):

    def test(self):
        zope.traversing.testing.setUp()

        root = Root()
        f1 = contained(C(), root, name='f1')
        f2 = contained(SiteManagerContainer(), f1, name='f2')
        f3 = contained(C(), f2, name='f3')
        
        adapter = ILocationInfo(f3)

        self.assertEqual(adapter.getPath(), '/f1/f2/f3')
        self.assertEqual(adapter.getName(), 'f3')
        self.assertEqual(adapter.getRoot(), root)
        self.assertEqual(adapter.getNearestSite(), root)

        f2.setSiteManager(LocalSiteManager(f2))
        self.assertEqual(adapter.getNearestSite(), f2)

        
def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')
