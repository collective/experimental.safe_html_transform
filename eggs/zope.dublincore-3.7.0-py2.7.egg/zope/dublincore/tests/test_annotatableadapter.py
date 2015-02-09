##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
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
"""Tests annotatableadapter.
"""
import unittest

_marker = object()

class ZDCAnnotatableAdapterTests(unittest.TestCase):

    _registered = False

    def setUp(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def tearDown(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def _getTargetClass(self):
        from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
        return ZDCAnnotatableAdapter

    def _registerAnnotations(self, dcdata=None):
        from zope.component import provideAdapter
        from zope.interface import Interface
        from zope.annotation.interfaces import IAnnotations
        from zope.dublincore.annotatableadapter import DCkey
        class _Annotations(dict):
            pass
        instance = _Annotations({DCkey: dcdata})
        def _factory(context):
            return instance
        if not self._registered:
            provideAdapter(_factory, (Interface, ), IAnnotations)
            self._registered = True
            return instance

    def _makeOne(self, context=_marker):
        if context is _marker:
            context = self._makeContext()
        return self._getTargetClass()(context)

    def _makeContext(self):
        class DummyContext(object):
            pass
        return DummyContext()

    def test_class_conforms_to_IWriteZopeDublinCore(self):
        from zope.interface.verify import verifyClass
        from zope.dublincore.interfaces import IWriteZopeDublinCore
        verifyClass(IWriteZopeDublinCore, self._getTargetClass())

    def test_instance_conforms_to_IWriteZopeDublinCore(self):
        from zope.interface.verify import verifyObject
        from zope.dublincore.interfaces import IWriteZopeDublinCore
        self._registerAnnotations()
        verifyObject(IWriteZopeDublinCore, self._makeOne())

    def test_ctor_wo_existing_DC_annotations(self):
        from zope.dublincore.annotatableadapter import DCkey
        self._registerAnnotations()
        context = self._makeContext()
        adapter = self._makeOne(context)
        self.assertEqual(adapter.annotations[DCkey], None)
        self.assertEqual(adapter._mapping, {})

    def test_ctor_w_existing_DC_annotations(self):
        DCDATA = {'title': 'TITLE'}
        self._registerAnnotations(DCDATA)
        context = self._makeContext()
        adapter = self._makeOne(context)
        self.assertEqual(adapter.annotations, None)
        self.assertEqual(adapter._mapping, DCDATA)

    def test__changed_wo_existing_DC_annotations(self):
        from zope.dublincore.annotatableadapter import DCkey
        annotations = self._registerAnnotations()
        context = self._makeContext()
        adapter = self._makeOne(context)
        adapter._mapping['title'] = 'NEW TITLE'
        adapter._changed()
        self.assertEqual(annotations[DCkey]['title'], 'NEW TITLE')

    def test__changed_w_existing_DC_annotations(self):
        from zope.dublincore.annotatableadapter import DCkey
        DCDATA = {'title': 'TITLE'}
        annotations = self._registerAnnotations(DCDATA)
        context = self._makeContext()
        adapter = self._makeOne(context)
        adapter._changed()
        self.assertEqual(annotations[DCkey]['title'], 'TITLE') #unchanged

class DirectPropertyTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.dublincore.annotatableadapter import DirectProperty
        return DirectProperty

    def _makeOne(self, name, attrname):
        return self._getTargetClass()(name, attrname)

    def test___get___via_klass(self):
        prop = self._makeOne('title', 'headline')
        class Testing(object):
            title = prop
        self.failUnless(Testing.title is prop)

    def test___get___via_instance(self):
        prop = self._makeOne('title', 'headline')
        class Context(object):
            headline = u'HEADLINE'
        class ZDCPartialAnnotatableAdapter(object):
            title = prop
            def __init__(self, context):
                self.__context = context
        context = Context()
        testing = ZDCPartialAnnotatableAdapter(context)
        self.assertEqual(testing.title, u'HEADLINE')

    def test___set___non_unicode_raises(self):
        prop = self._makeOne('title', 'headline')
        class Context(object):
            headline = u'HEADLINE'
        class ZDCPartialAnnotatableAdapter(object):
            title = prop
            def __init__(self, context):
                self.__context = context
        context = Context()
        testing = ZDCPartialAnnotatableAdapter(context)
        try:
            testing.title = 123
        except TypeError:
            pass
        else:
            self.fail("Didn't raise TypeError")

    def test___set___unchanged_doesnt_mutate(self):
        prop = self._makeOne('title', 'headline')
        class Context(object):
            headline = u'HEADLINE'
            def __setattr__(self, name, value):
                assert 0
        class ZDCPartialAnnotatableAdapter(object):
            title = prop
            def __init__(self, context):
                self.__context = context
        context = Context()
        testing = ZDCPartialAnnotatableAdapter(context)
        testing.title = u'HEADLINE' # doesn't raise

    def test___set___changed_mutates(self):
        prop = self._makeOne('title', 'headline')
        class Context(object):
            headline = u'HEADLINE1'
        class ZDCPartialAnnotatableAdapter(object):
            title = prop
            def __init__(self, context):
                self.__context = context
        context = Context()
        testing = ZDCPartialAnnotatableAdapter(context)
        testing.title = u'HEADLINE2'
        self.assertEqual(context.headline, u'HEADLINE2')

class Test_partialAnnotatableAdapterFactory(unittest.TestCase):

    def _callFUT(self, direct_fields):
        from zope.dublincore.annotatableadapter \
            import partialAnnotatableAdapterFactory
        return partialAnnotatableAdapterFactory(direct_fields)

    def test_w_empty_list_raises(self):
        self.assertRaises(ValueError, self._callFUT, [])

    def test_w_empty_dict_raises(self):
        self.assertRaises(ValueError, self._callFUT, {})

    def test_w_unknown_field_raises(self):
        self.assertRaises(ValueError, self._callFUT, ['nonesuch'])

    def test_w_date_fields_raises(self):
        self.assertRaises(ValueError, self._callFUT, ['created'])
        self.assertRaises(ValueError, self._callFUT, ['modified'])
        self.assertRaises(ValueError, self._callFUT, ['effective'])
        self.assertRaises(ValueError, self._callFUT, ['expires'])

    def test_w_sequence_fields_raises(self):
        self.assertRaises(ValueError, self._callFUT, ['creators'])
        self.assertRaises(ValueError, self._callFUT, ['subjects'])
        self.assertRaises(ValueError, self._callFUT, ['contributors'])

    def test_w_scalar_prop_samename(self):
        from zope.dublincore.annotatableadapter import DirectProperty
        klass = self._callFUT(['title'])
        prop = klass.title
        self.failUnless(isinstance(prop, DirectProperty))
        self.assertEqual(prop.__name__, 'title')
        self.assertEqual(prop._DirectProperty__attrname, 'title') # XXX

    def test_w_scalar_prop_mapped(self):
        from zope.dublincore.annotatableadapter import DirectProperty
        klass = self._callFUT({'title': 'headline'})
        prop = klass.title
        self.failUnless(isinstance(prop, DirectProperty))
        self.assertEqual(prop.__name__, 'title')
        self.assertEqual(prop._DirectProperty__attrname, 'headline') # XXX


def test_suite():
    return unittest.TestSuite((
            unittest.makeSuite(ZDCAnnotatableAdapterTests),
            unittest.makeSuite(DirectPropertyTests),
            unittest.makeSuite(Test_partialAnnotatableAdapterFactory),
        ))

