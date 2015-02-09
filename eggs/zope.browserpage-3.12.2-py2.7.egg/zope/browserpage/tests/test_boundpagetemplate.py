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
"""Bound Page Template Tests

$Id: test_boundpagetemplate.py 111996 2010-05-05 17:34:04Z tseaver $
"""
import unittest

class Test(unittest.TestCase):

    def testAttributes(self):

        from zope.browserpage.tests.sample import C

        C.index.im_func.foo = 1
        self.assertEqual(C.index.macros, C.index.im_func.macros)
        self.assertEqual(C.index.filename, C.index.im_func.filename)



def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
