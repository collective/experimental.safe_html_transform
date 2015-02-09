##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""Tests of combining ZopeVersionControl with the References product.

$Id: testReferenceVersioning.py 113728 2010-06-21 15:10:46Z ctheune $
"""
import unittest

from common import common_setUp
from common import common_tearDown

has_refs = 1
try:
    from Products.References.PathReference import PathReference
except ImportError:
    has_refs = 0

class ReferenceVCTests(unittest.TestCase):

    setUp = common_setUp
    tearDown = common_tearDown

    def testContainerVersioning(self):
        # Verify that containers and items are versioned independently,
        # except in the case of references.
        from OFS.DTMLDocument import addDTMLDocument

        repository = self.repository
        folder1 = self.app.folder1
        folder2 = folder1.folder2
        folder1.testattr = 'container_v1'
        folder2.testattr = 'item_v1'
        folder1._setOb("ref", PathReference("ref", folder1.folder2))
        folder2._true_id = "folder2"
        self.assertEqual(folder1.ref._true_id, "folder2")

        self.assert_(not repository.isUnderVersionControl(folder1))
        repository.applyVersionControl(folder1)
        folder1 = self.app.folder1
        self.assert_(repository.isUnderVersionControl(folder1))
        self.assert_(not repository.isUnderVersionControl(folder2))
        self.assert_(not repository.isUnderVersionControl(folder1.ref))
        repository.applyVersionControl(folder2)
        folder2 = folder1.folder2
        self.assert_(repository.isUnderVersionControl(folder2))
        self.assert_(not repository.isUnderVersionControl(folder2.document1))

        # Make the first version of folder1 and check it in.
        repository.checkoutResource(folder1)
        folder1 = self.app.folder1
        repository.checkinResource(folder1)
        folder1 = self.app.folder1
        folder2 = folder1.folder2
        info = repository.getVersionInfo(folder1)
        first_version = info.version_id

        # Change folder1 and check it in again
        repository.checkoutResource(folder1)
        folder1 = self.app.folder1
        folder1.testattr = 'container_v2'
        addDTMLDocument(folder1, 'document3', file='some more text')
        folder1.document3._true_id = "document3"
        repository.checkinResource(folder1)
        folder1 = self.app.folder1
        folder2 = folder1.folder2

        # Change ref to point to document3.
        folder1._delObject("ref")
        folder1._setOb("ref", PathReference("ref", folder1.document3))
        self.assertEqual(folder1.ref._true_id, "document3")

        # Change folder2
        repository.checkoutResource(folder2)
        folder2 = folder1.folder2
        folder2.testattr = 'item_v2'

        # Now revert folder1 and verify that folder2 was not reverted.
        # Also verify that ref now points back to folder2.
        repository.updateResource(folder1, first_version)
        folder1 = self.app.folder1
        folder2 = folder1.folder2
        self.assertEqual(folder1.testattr, 'container_v1')
        self.assertEqual(folder2.testattr, 'item_v2')
        self.assertEqual(folder1.ref._true_id, "folder2")

        # Verify that document3 remains an item of the reverted folder1.
        self.assert_(hasattr(folder1, 'document3'))
        self.assert_(str(folder1.document3) == 'some more text')

        # Remove document3 and verify that it doesn't reappear upon revert.
        folder1._delObject('document3')
        repository.updateResource(folder1, '')
        folder1 = self.app.folder1
        self.assertEqual(folder1.testattr, 'container_v2')
        self.assertEqual(folder1.folder2.testattr, 'item_v2')
        self.assert_(not hasattr(folder1, 'document3'))


def test_suite():
    suite = unittest.TestSuite()
    if has_refs:
        suite.addTest(unittest.makeSuite(ReferenceVCTests))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')

