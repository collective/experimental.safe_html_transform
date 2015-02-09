from zope.interface import alsoProvides, noLongerProvides
from Products.ATContentTypes.content.document import ATDocument
from Products.CMFDiffTool.ATCompoundDiff import ATCompoundDiff

import BaseTestCase
from zope.component import adapts, provideAdapter
from Products.Archetypes import atapi

class TestATCompoundDiff(BaseTestCase.ATBaseTestCase):
    """Test the portal_diff tool"""

    def testCompoundDiff(self):
        first = self.folder.invokeFactory('Document', 'extended-document')
        first = self.folder[first]
        second = self.folder.invokeFactory('Document', 'extended-document2')
        second = self.folder[second]
        # Change a value
        first.setText('<p>Body1</p>', mimetype='text/html')
        second.setText('<p>Body2</p>', mimetype='text/html')
        fd = ATCompoundDiff(first, second, None)
        # There should be some fields
        self.failUnless(len(fd))
        for field in fd:
            # We've changed the body
            if field.label == 'label_body_text':
                # We have the correct values
                self.assertEqual(field.oldValue, '<p>Body1</p>')
                self.assertEqual(field.newValue, '<p>Body2</p>')
                # And the correctly assigned diff type
                self.assertEqual(field.meta_type, 'HTML Diff')
            # We've also changed the id
            elif field.label == 'label_short_name':
                self.assertEqual(field.oldValue, 'extended-document')
                self.assertEqual(field.newValue, 'extended-document2')
                self.assertEqual(field.meta_type, 'Lines Diff')
            # The dates will be different, but everything else should
            # be the same
            elif field.label not in ('label_creation_date',
                                     'label_modification_date'):
                self.assertEqual(field.oldValue, field.newValue)

    def testAdaptedObjects(self):
        # Add a schema extended field to an ATDocument and test that
        # the compound diff can read it
        if not BaseTestCase.HAS_AT_SCHEMA_EXTENDER:
            return
        from archetypes.schemaextender.field import ExtensionField
        from archetypes.schemaextender.tests.mocks import IHighlighted, Extender

        # custom field class which does not set attributes directly on the
        # content
        class HighlightedField(ExtensionField, atapi.StringField):
            def get(self, instance, **kwargs):
                return IHighlighted.providedBy(instance)
            def getRaw(self, instance, **kwargs):
                return self.get(instance, **kwargs)
            def set(self, instance, value, **kwargs):
                if value and not IHighlighted.providedBy(instance):
                    alsoProvides(instance, IHighlighted)
                elif not value and IHighlighted.providedBy(instance):
                    noLongerProvides(instance, IHighlighted)

        class TestSchemaExtender(Extender):
            adapts(ATDocument)
            fields = [
                HighlightedField('schemaextender_test',
                                 schemata='settings',
                                 widget=atapi.BooleanWidget(
                                                    label="Extended",
                                                    description=""),
                                 ),
                      ]

        """Ensure that tool instances implement the portal_diff interface"""
        provideAdapter(TestSchemaExtender,
                       name=u"archetypes.schemaextender.tests")

        first = self.folder.invokeFactory('Document', 'extended-document')
        first = self.folder[first]
        second = self.folder.invokeFactory('Document', 'extended-document2')
        second = self.folder[second]
        # Change the value
        alsoProvides(second, IHighlighted)
        fd = ATCompoundDiff(first, second, None)
        field = fd[-1]
        self.assertEqual(field.oldValue, False)
        self.assertEqual(field.newValue, True)
        self.assertEqual(field.label, "Extended")
