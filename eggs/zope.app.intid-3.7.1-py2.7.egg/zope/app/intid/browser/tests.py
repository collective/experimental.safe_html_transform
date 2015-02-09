##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Int Id Utility Functional Tests

$Id: tests.py 95789 2009-01-31 20:19:05Z nadako $
"""
import unittest
from zope.app.testing import functional
from zope.app.intid.testing import IntIdLayer

from transaction import commit

from zope.app.testing import setup, ztapi
from zope.app.testing.functional import BrowserTestCase

from zope.intid import IntIds, intIdEventNotify
from zope.intid.interfaces import IIntIds
from zope.traversing.api import traverse

class TestFunctionalIntIds(BrowserTestCase):

    def setUp(self):
        BrowserTestCase.setUp(self)

        self.basepath = '/++etc++site/default'
        root = self.getRootFolder()

        sm = traverse(root, '/++etc++site')
        setup.addUtility(sm, 'intid', IIntIds, IntIds())
        commit()

        type_name = 'BrowserAdd__zope.intid.IntIds'

        response = self.publish(
            self.basepath + '/contents.html',
            basic='mgr:mgrpw',
            form={'type_name': type_name,
                  'new_value': 'mgr' })

    def test(self):
        response = self.publish(self.basepath + '/intid/@@index.html',
                                basic='mgr:mgrpw')
        self.assertEquals(response.getStatus(), 200)
        # The utility registers in itself when it is being added
        self.assert_(response.getBody().find('1 objects') > 0)
        self.assert_('<a href="/++etc++site">/++etc++site</a>'
                     not in response.getBody())

        response = self.publish(self.basepath + '/intid/@@populate',
                                basic='mgr:mgrpw')
        self.assertEquals(response.getStatus(), 302)

        response = self.publish(self.basepath
                                + '/intid/@@index.html?testing=1',
                                basic='mgr:mgrpw')
        self.assertEquals(response.getStatus(), 200)
        body = response.getBody()
        self.assert_('3 objects' in body)
        self.assert_('<a href="/++etc++site">/++etc++site</a>' in body)
        self.checkForBrokenLinks(body, response.getPath(), basic='mgr:mgrpw')

def test_suite():
    TestFunctionalIntIds.layer = IntIdLayer
    browser = unittest.makeSuite(TestFunctionalIntIds)
    tracking = functional.FunctionalDocFileSuite('tracking.txt')
    tracking.layer = IntIdLayer
    return unittest.TestSuite((browser, tracking))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
