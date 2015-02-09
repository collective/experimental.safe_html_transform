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
"""Test the VersionHistory internals.

$Id: testVersionHistory.py 116297 2010-09-10 18:29:06Z dtremea $
"""
import unittest

from common import common_setUp
from common import common_tearDown


class VersionHistoryTests(unittest.TestCase):

    setUp = common_setUp
    tearDown = common_tearDown

    def testBranchHaveName(self):
        self.repository.applyVersionControl(self.document1)
        info = self.repository.getVersionInfo(self.document1)
        history = self.repository.getVersionHistory(info.history_id)
        branch = history.createBranch('foo', None)
        self.assertEqual(branch.getId(), 'foo')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(VersionHistoryTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
