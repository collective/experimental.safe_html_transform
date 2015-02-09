##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for browser module.

$Id: tests.py 113210 2010-06-06 15:09:46Z hannosch $
"""

import unittest
from Testing import ZopeTestCase
try:
    from Zope2.App.schema import Zope2VocabularyRegistry
except ImportError:  # Zope2 <= 2.12
    from Products.Five.schema import Zope2VocabularyRegistry

from Products.CMFCalendar.testing import FunctionalLayer

def _setupVocabulary(ztc):
    from zope.schema.vocabulary import setVocabularyRegistry
    setVocabularyRegistry(Zope2VocabularyRegistry())

def _clearVocabulary(ztc):
    from zope.schema.vocabulary import _clear
    _clear()
    

def test_suite():
    suite = unittest.TestSuite()
    s = ZopeTestCase.FunctionalDocFileSuite('event.txt',
                                            setUp=_setupVocabulary,
                                            tearDown=_clearVocabulary,
                                           )
    s.layer = FunctionalLayer
    suite.addTest(s)
    return suite

if __name__ == '__main__':
    from Products.CMFCore.testing import run
    run(test_suite())
