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
"""Tests creator annotation.
"""
import unittest

class CreatorAnnotatorTests(unittest.TestCase):

    def setUp(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()
        self._makeInterface()
        self._registerAdapter()

    def tearDown(self):
        from zope.testing.cleanup import cleanUp
        from zope.security.management import endInteraction
        endInteraction()
        cleanUp()

    def _callFUT(self, event):
        from zope.dublincore.creatorannotator import CreatorAnnotator
        return CreatorAnnotator(event)

    def _makeInterface(self):
        from zope.interface import Interface

        class IDummyContent(Interface):
            pass

        self._iface = IDummyContent

    def _registerAdapter(self):
        from zope.component import provideAdapter
        from zope.dublincore.interfaces import IZopeDublinCore
        provideAdapter(DummyDCAdapter, (self._iface, ), IZopeDublinCore)

    def _makeContextAndEvent(self):

        from zope.interface import implements

        class DummyDublinCore(object):
            implements(self._iface)
            creators = ()

        class DummyEvent(object):
            def __init__(self, object):
                self.object = object

        context = DummyDublinCore()
        event = DummyEvent(context)
        return context, event

    def _setPrincipal(self, id):
        from zope.security.management import newInteraction
        class DummyPrincipal(object):
            title = 'TITLE'
            description = 'DESCRIPTION'
            def __init__(self, id):
                self.id = id
        if id is None:
            newInteraction(DummyRequest(None))
        else:
            newInteraction(DummyRequest(DummyPrincipal(id)))

    def test_w_no_request(self):
        context, event = self._makeContextAndEvent()
        self._callFUT(event)
        self.assertEqual(context.creators, ())

    def test_w_request_no_existing_creators(self):
        context, event = self._makeContextAndEvent()
        self._setPrincipal('phred')
        self._callFUT(event)
        self.assertEqual(context.creators, ('phred',))

    def test_w_request_w_existing_creator_nomatch(self):
        context, event = self._makeContextAndEvent()
        context.creators = ('bharney',)
        self._setPrincipal('phred')
        self._callFUT(event)
        self.assertEqual(context.creators, ('bharney', 'phred',))

    def test_w_request_w_existing_creator_match(self):
        context, event = self._makeContextAndEvent()
        context.creators = ('bharney', 'phred')
        self._setPrincipal('phred')
        self._callFUT(event)
        self.assertEqual(context.creators, ('bharney', 'phred',))

    def test_w_request_no_principal(self):
        context, event = self._makeContextAndEvent()
        context.creators = ('bharney', 'phred')
        self._setPrincipal(None)
        self._callFUT(event)
        self.assertEqual(context.creators, ('bharney', 'phred',))

class DummyDCAdapter(object):

    def _getcreator(self):
        return self.context.creators
    def _setcreator(self, value):
        self.context.creators = value
    creators = property(_getcreator, _setcreator, None, "Adapted Creators")

    def __init__(self, context):
        self.context = context


class DummyRequest(object):

    def __init__(self, principal):
        self.principal = principal
        self.interaction = None


def test_suite():
    return unittest.TestSuite((
            unittest.makeSuite(CreatorAnnotatorTests),
        ))
