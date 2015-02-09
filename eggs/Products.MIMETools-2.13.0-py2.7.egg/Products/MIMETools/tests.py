##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import unittest


class MimeTest(unittest.TestCase):

    def _getTargetClass(self):
        from Products.MIMETools import MIMETag
        return MIMETag.MIMETag

    def _makeOne(self, blocks=[]):
        klass = self._getTargetClass()
        return klass(blocks)

    def test_registered(self):
        klass = self._getTargetClass()
        from DocumentTemplate.DT_String import String
        self.failUnless('mime' in String.commands)
        self.failUnless(String.commands['mime'] is klass)

    def test_init(self):
        tag = self._makeOne()
        self.assertEquals(tag.sections, [])

    def test_render(self):
        tag = self._makeOne()
        result = tag.render(md={})
        self.assert_("Mime-Version: 1.0" in result)
        self.assert_("Content-Type: multipart/mixed;" in result)

    def test_call(self):
        tag = self._makeOne()
        result = tag(md={})
        self.assert_("Mime-Version: 1.0" in result)
        self.assert_("Content-Type: multipart/mixed;" in result)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MimeTest))
    return suite
