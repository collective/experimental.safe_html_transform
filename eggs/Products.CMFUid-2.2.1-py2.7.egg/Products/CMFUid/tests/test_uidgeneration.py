##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test the unique id generation.

$Id: test_uidgeneration.py 110665 2010-04-08 16:12:03Z tseaver $
"""

import unittest
import Testing

from BTrees.Length import Length
from zope.interface.verify import verifyClass

from Products.CMFCore.tests.base.testcase import SecurityTest


class UniqueIdGeneratorToolTests(SecurityTest):

    def _getTargetClass(self):
        from Products.CMFUid.UniqueIdGeneratorTool \
                import UniqueIdGeneratorTool

        return UniqueIdGeneratorTool

    def setUp(self):
        SecurityTest.setUp(self)
        self.root._setObject('portal_uidgenerator', self._getTargetClass()())

    def test_interfaces(self):
        from Products.CMFUid.interfaces import IUniqueIdGenerator

        verifyClass(IUniqueIdGenerator, self._getTargetClass())

    def test_returnedUidsAreValidAndDifferent(self):
        generator = self.root.portal_uidgenerator
        uid1 = generator()
        uid2 = generator()
        self.failIfEqual(uid1, uid2)
        self.failIfEqual(uid1, None)

    def test_converter(self):
        generator = self.root.portal_uidgenerator
        uid = generator()
        str_uid = str(uid)
        result = generator.convert(str_uid)
        self.assertEqual(result, uid)

    def test_migrationFromBTreeLengthToInteger(self):
        # For backwards compatibility with CMF 1.5.0 and 1.5.1, check if
        # the generator correctly replaces a ``BTree.Length.Length`` object
        # to an integer.
        generator = self.root.portal_uidgenerator
        uid1 = generator()
        generator._uid_counter = Length(uid1)
        self.failUnless(isinstance(generator._uid_counter, Length))
        uid2 = generator()
        self.failUnless(isinstance(generator._uid_counter, int))
        self.failIfEqual(uid1, uid2)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UniqueIdGeneratorToolTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
