##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Shared utility functions for browser view tests """

try:
    from Zope2.App.schema import Zope2VocabularyRegistry
except ImportError:  # Zope2 <= 2.12
    from Products.Five.schema import Zope2VocabularyRegistry


def setupVocabulary(testcase):
    from zope.schema.vocabulary import setVocabularyRegistry
    setVocabularyRegistry(Zope2VocabularyRegistry())

def clearVocabulary(testcase):
    from zope.schema.vocabulary import _clear
    _clear()
