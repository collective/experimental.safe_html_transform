##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import transaction
from unittest import TestCase, makeSuite
from Products.Transience.TransactionHelper import PreventTransactionCommit, \
         makeTransactionUncommittable


class TestTransactionHelper(TestCase):
    def setUp(self):
        self.t = transaction.get()

    def tearDown(self):
        self.t = None

    def testUncommittable(self):
        makeTransactionUncommittable(self.t, "test")
        self.assertRaises(PreventTransactionCommit, transaction.commit)
        transaction.abort()


def test_suite():
    suite = makeSuite(TestTransactionHelper, 'test')
    return suite
