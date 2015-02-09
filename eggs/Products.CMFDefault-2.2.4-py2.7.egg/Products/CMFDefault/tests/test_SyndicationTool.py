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
""" Unit tests for SyndicationTool module. """

import unittest
import Testing

from DateTime.DateTime import DateTime
from zope.interface.verify import verifyClass
from zope.testing.cleanup import cleanUp

from Products.CMFCore.tests.base.testcase import SecurityTest


class Dummy:

    def getId(self):
        return 'dummy'


class SyndicationToolTests(SecurityTest):

    def _getTargetClass(self):
        from Products.CMFDefault.SyndicationTool import SyndicationTool
        return SyndicationTool

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)

    def test_interfaces(self):
        from Products.CMFCore.interfaces import ISyndicationTool

        verifyClass(ISyndicationTool, self._getTargetClass())

    def test_empty(self):
        ONE_MINUTE = (24.0 * 60.0) / 86400

        tool = self._makeOne()

        self.assertEqual(tool.syUpdatePeriod, 'daily')
        self.assertEqual(tool.syUpdateFrequency, 1)
        self.failUnless(DateTime() - tool.syUpdateBase < ONE_MINUTE)
        self.failIf(tool.isAllowed)
        self.assertEqual(tool.max_items, 15)

    def test_editProperties_normal(self):
        PERIOD = 'hourly'
        FREQUENCY = 4
        NOW = DateTime()
        MAX_ITEMS = 42

        tool = self._makeOne()
        tool.editProperties(updatePeriod=PERIOD,
                            updateFrequency=FREQUENCY,
                            updateBase=NOW,
                            isAllowed=True,
                            max_items=MAX_ITEMS,
                           )

        self.assertEqual(tool.syUpdatePeriod, PERIOD)
        self.assertEqual(tool.syUpdateFrequency, FREQUENCY)
        self.assertEqual(tool.syUpdateBase, NOW)
        self.failUnless(tool.isAllowed)
        self.assertEqual(tool.max_items, MAX_ITEMS)

    def test_editProperties_coercing(self):
        PERIOD = 'hourly'
        FREQUENCY = 4
        NOW = DateTime()
        MAX_ITEMS = 42

        tool = self._makeOne()
        tool.editProperties(updatePeriod=PERIOD,
                            updateFrequency='%d' % FREQUENCY,
                            updateBase=NOW.ISO(),
                            isAllowed='True',
                            max_items='%d' % MAX_ITEMS,
                           )

        self.assertEqual(tool.syUpdatePeriod, PERIOD)
        self.assertEqual(tool.syUpdateFrequency, FREQUENCY)
        self.assertEqual(tool.syUpdateBase, DateTime(NOW.ISO()))
        self.failUnless(tool.isAllowed)
        self.assertEqual(tool.max_items, MAX_ITEMS)

    def test_editSyInformationProperties_disabled(self):
        from zExceptions import Unauthorized

        tool = self._makeOne()
        dummy = Dummy()
        try:
            tool.editSyInformationProperties(object, updateFrequency=1)
        except Unauthorized:
            raise
        except: # WAAA! it raises a string!
            pass
        else:
            assert 0, "Didn't raise"

    def test_editSyInformationProperties_normal(self):
        PERIOD = 'hourly'
        FREQUENCY = 4
        NOW = DateTime()
        MAX_ITEMS = 42

        tool = self._makeOne()
        dummy = Dummy()
        info = dummy.syndication_information = Dummy()

        tool.editSyInformationProperties(dummy,
                                         updatePeriod=PERIOD,
                                         updateFrequency=FREQUENCY,
                                         updateBase=NOW,
                                         max_items=MAX_ITEMS,
                                        )

        self.assertEqual(info.syUpdatePeriod, PERIOD)
        self.assertEqual(info.syUpdateFrequency, FREQUENCY)
        self.assertEqual(info.syUpdateBase, NOW)
        self.assertEqual(info.max_items, MAX_ITEMS)

    def test_editSyInformationProperties_coercing(self):
        PERIOD = 'hourly'
        FREQUENCY = 4
        NOW = DateTime()
        MAX_ITEMS = 42

        tool = self._makeOne()
        dummy = Dummy()
        info = dummy.syndication_information = Dummy()

        tool.editSyInformationProperties(dummy,
                                         updatePeriod=PERIOD,
                                         updateFrequency='%d' % FREQUENCY,
                                         updateBase=NOW.ISO(),
                                         max_items='%d' % MAX_ITEMS,
                                        )

        self.assertEqual(info.syUpdatePeriod, PERIOD)
        self.assertEqual(info.syUpdateFrequency, FREQUENCY)
        self.assertEqual(info.syUpdateBase, DateTime(NOW.ISO()))
        self.assertEqual(info.max_items, MAX_ITEMS)

    def test_editProperties_isAllowedOnly(self):
        # Zope 2.8 crashes if we don't edit all properties.
        # This is because Zope now raises AttributeError
        # instead of KeyError in editProperties().
        tool = self._makeOne()
        tool.editProperties(isAllowed=1)

        self.failUnless(tool.isAllowed)

    def test_getSyndicatableContent(self):
        # http://www.zope.org/Collectors/CMF/369
        # Make sure we use a suitable base class call when determining
        # syndicatable content
        from Products.CMFCore.PortalFolder import PortalFolder
        from Products.CMFCore.CMFBTreeFolder import CMFBTreeFolder
        from Products.CMFCore.TypesTool import TypesTool

        PERIOD = 'hourly'
        FREQUENCY = 4
        NOW = DateTime()
        MAX_ITEMS = 42

        self.root._setObject( 'portal_types', TypesTool() )
        self.root._setObject('pf', PortalFolder('pf'))
        self.root._setObject('bf', CMFBTreeFolder('bf'))
        self.root._setObject('portal_syndication', self._makeOne())
        tool = self.root.portal_syndication
        tool.editProperties(updatePeriod=PERIOD,
                            updateFrequency=FREQUENCY,
                            updateBase=NOW,
                            isAllowed=True,
                            max_items=MAX_ITEMS,
                           )

        self.assertEqual(len(tool.getSyndicatableContent(self.root.pf)), 0)
        self.assertEqual(len(tool.getSyndicatableContent(self.root.bf)), 0)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(SyndicationToolTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
