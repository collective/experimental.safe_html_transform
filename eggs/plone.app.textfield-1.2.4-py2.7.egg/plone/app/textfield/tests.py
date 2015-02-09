import doctest
import unittest

import plone.app.textfield
from plone.app.testing.bbb import PloneTestCase
from plone.app import testing
from plone.testing import layered


class IntegrationFixture(testing.PloneSandboxLayer):

    defaultBases = (testing.PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=plone.app.textfield)

PTC_FIXTURE = IntegrationFixture()
IntegrationLayer = testing.FunctionalTesting(
    bases=(PTC_FIXTURE, ), name='PloneAppTextfieldTest:Functional')


class TestIntegration(PloneTestCase):

    layer = IntegrationLayer

    def testTransformPlain(self):
        from zope.interface import Interface
        from plone.app.textfield import RichText

        class IWithText(Interface):

            text = RichText(title=u"Text",
                            default_mime_type='text/plain',
                            output_mime_type='text/html')

        value = IWithText['text'].fromUnicode(u"Some **text**")
        self.assertEquals(u'<p>Some **text**</p>', value.output)

    def testTransformNone(self):
        from plone.app.textfield.value import RichTextValue
        value = RichTextValue()
        # Mostly, these calls simply should not give an error.
        self.assertEquals(None, value.raw)
        self.assertEquals(u'', value.output)

    def testTransformStructured(self):
        from zope.interface import Interface
        from plone.app.textfield import RichText

        class IWithText(Interface):

            text = RichText(title=u"Text",
                            default_mime_type='text/structured',
                            output_mime_type='text/html')

        value = IWithText['text'].fromUnicode(u"Some **text**")
        self.assertEquals(u'<p>Some <strong>text</strong></p>\n', value.output)

    def testTransformView(self):
        from zope.interface import Interface, implements
        from plone.app.textfield import RichText
        from Products.CMFCore.PortalContent import PortalContent

        class IWithText(Interface):

            text = RichText(title=u"Text",
                            default_mime_type='text/structured',
                            output_mime_type='text/html')

        class Context(PortalContent):
            implements(IWithText)

            id = 'context'
            text = None

        context = Context()
        context.text = IWithText['text'].fromUnicode(u"Some **text**")

        self.portal._setObject('context', context)
        context = self.portal['context']

        output = context.restrictedTraverse('@@text-transform/text')()
        self.assertEquals(u'<p>Some <strong>text</strong></p>', output.strip())

        output = context.restrictedTraverse('@@text-transform/text/text/plain')()
        self.assertEquals(u'Some text', output.strip())

        # test transform shortcircuit when input and output type is the
        # same. this used to cause infinite recursion
        class IWithText(Interface):
            text = RichText(title=u"Text",
                            default_mime_type='text/html',
                            output_mime_type='text/html')

        context.text = IWithText['text'].fromUnicode(u"<span>Some html</span>")
        output = context.restrictedTraverse('@@text-transform/text')()
        self.assertEquals(u"<span>Some html</span>", output.strip())

    def testTransformNoneView(self):
        from zope.interface import Interface, implements
        from plone.app.textfield import RichText
        from plone.app.textfield.value import RichTextValue
        from Products.CMFCore.PortalContent import PortalContent

        class IWithText(Interface):

            text = RichText(title=u"Text",
                            default_mime_type='text/structured',
                            output_mime_type='text/html')

        class Context(PortalContent):
            implements(IWithText)

            id = 'context'
            text = None

        context = Context()
        # None as value should not lead to errors.
        context.text = RichTextValue()

        self.portal._setObject('context', context)
        context = self.portal['context']

        output = context.restrictedTraverse('@@text-transform/text')()
        self.assertEquals(u'', output.strip())

        output = context.restrictedTraverse('@@text-transform/text/text/plain')()
        self.assertEquals(u'', output.strip())

    def testWidgetExtract(self):
        from zope.interface import Interface, implements
        from plone.app.textfield import RichText
        from zope.publisher.browser import TestRequest
        from Products.CMFCore.PortalContent import PortalContent
        from plone.app.textfield.widget import RichTextWidget
        from z3c.form.widget import FieldWidget
        from z3c.form.interfaces import NOVALUE

        class IWithText(Interface):

            text = RichText(title=u"Text",
                            default_mime_type='text/structured',
                            output_mime_type='text/html')

        class Context(PortalContent):
            implements(IWithText)

            text = None

        request = TestRequest()

        widget = FieldWidget(IWithText['text'], RichTextWidget(request))
        widget.update()

        value = widget.extract()
        self.assertEquals(NOVALUE, value)

        request.form['%s' % widget.name] = u"Sample **text**"
        request.form['%s.mimeType' % widget.name] = 'text/structured'

        value = widget.extract()
        self.assertEquals(u"<p>Sample <strong>text</strong></p>", value.output.strip())

    def testWidgetConverter(self):
        from zope.interface import Interface
        from plone.app.textfield import RichText
        from zope.publisher.browser import TestRequest
        from plone.app.textfield.value import RichTextValue
        from plone.app.textfield.widget import RichTextWidget, RichTextConverter
        from z3c.form.widget import FieldWidget

        _marker = object()

        class IWithText(Interface):

            text = RichText(title=u"Text",
                            default_mime_type='text/structured',
                            output_mime_type='text/html',
                            missing_value=_marker)

        request = TestRequest()

        widget = FieldWidget(IWithText['text'], RichTextWidget(request))
        widget.update()

        converter = RichTextConverter(IWithText['text'], widget)
        self.assertTrue(converter.toFieldValue(u'') is _marker)
        self.assertTrue(converter.toFieldValue(RichTextValue(u'')) is _marker)

    def testWidgetAllowedTypesDefault(self):
        from zope.interface import Interface, implements
        from plone.app.textfield import RichText
        from zope.publisher.browser import TestRequest
        from Products.CMFCore.PortalContent import PortalContent
        from plone.app.textfield.widget import RichTextWidget
        from z3c.form.widget import FieldWidget

        class IWithText(Interface):

            text = RichText(title=u"Text",
                            default_mime_type='text/structured',
                            output_mime_type='text/html')

        class Context(PortalContent):
            implements(IWithText)

            text = None

        request = TestRequest()

        widget = FieldWidget(IWithText['text'], RichTextWidget(request))
        widget.update()

        self.portal['portal_properties']['site_properties']._setPropValue('forbidden_contenttypes', ['text/structured'])

        allowed = widget.allowedMimeTypes()
        self.failUnless('text/html' in allowed)
        self.failIf('text/structured' in allowed)

    def testWidgetAllowedTypesField(self):
        from zope.interface import Interface, implements
        from plone.app.textfield import RichText
        from zope.publisher.browser import TestRequest
        from Products.CMFCore.PortalContent import PortalContent
        from plone.app.textfield.widget import RichTextWidget
        from z3c.form.widget import FieldWidget

        class IWithText(Interface):

            text = RichText(title=u"Text",
                            default_mime_type='text/structured',
                            output_mime_type='text/html',
                            allowed_mime_types=('text/structured', 'text/html'))

        class Context(PortalContent):
            implements(IWithText)

            text = None

        request = TestRequest()

        widget = FieldWidget(IWithText['text'], RichTextWidget(request))
        widget.update()

        self.portal['portal_properties']['site_properties']._setPropValue('forbidden_contenttypes', ['text/structured'])

        allowed = widget.allowedMimeTypes()
        self.failUnless('text/html' in allowed)
        self.failUnless('text/structured' in allowed)


def test_suite():
    suite = unittest.makeSuite(TestIntegration)
    for doctestfile in ['field.rst', 'handler.rst', 'marshaler.rst']:
        suite.addTest(layered(
            doctest.DocFileSuite(doctestfile, optionflags=doctest.ELLIPSIS),
            layer=testing.PLONE_FIXTURE))
    return suite
