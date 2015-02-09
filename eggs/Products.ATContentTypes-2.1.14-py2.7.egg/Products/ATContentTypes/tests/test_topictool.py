import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase

from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.config import TOOLNAME
from Products.ATContentTypes.interfaces import IATCTTopicsTool
from zope.interface.verify import verifyObject

tests = []
index_def = {'index': 'end',
             'friendlyName': 'End Date For Test',
             'description': 'This is an end Date',
             'criteria': ['ATDateCriteria', 'ATDateRangeCriteria']
            }
meta_def = {'metadata': 'ModificationDate',
            'friendlyName': 'Modification Date For Test',
            'description': ''
           }


class TestTool(atcttestcase.ATCTSiteTestCase):

    def afterSetUp(self):
        self.tool = getattr(self.portal.aq_explicit, TOOLNAME)

    def test_interface(self):
        self.assertTrue(IATCTTopicsTool.providedBy(self.tool))
        self.assertTrue(verifyObject(IATCTTopicsTool, self.tool))

    #Index tests
    def test_add_index(self):
        t = self.tool
        t.addIndex(enabled=True, **index_def)
        index = t.getIndex(index_def['index'])
        self.assertEqual(index.index, index_def['index'])
        self.assertEqual(index.friendlyName, index_def['friendlyName'])
        self.assertEqual(index.description, index_def['description'])
        # Only need to test truth not actual value
        self.assertTrue(index.enabled)
        self.assertEqual(index.criteria, tuple(index_def['criteria']))

        self.assertTrue(index in t.getEnabledIndexes())
        self.assertTrue(index_def['index'] in [a[0] for a in t.getEnabledFields()])
        self.assertTrue(index_def['index'] in t.getIndexDisplay(True).keys())
        self.assertTrue(index_def['friendlyName'] in t.getIndexDisplay(True).values())
        self.assertTrue(index_def['index'] in t.getIndexes(1))

    def test_disable_index(self):
        t = self.tool
        t.addIndex(enabled=False, **index_def)
        index = t.getIndex(index_def['index'])
        self.assertEqual(index.index, index_def['index'])
        self.assertEqual(index.friendlyName, index_def['friendlyName'])
        self.assertEqual(index.description, index_def['description'])
        # Only need to test truth not actual value
        self.assertFalse(index.enabled)
        self.assertEqual(index.criteria, tuple(index_def['criteria']))

        self.assertFalse(index in t.getEnabledIndexes())
        self.assertFalse(index_def['index'] in [a[0] for a in t.getEnabledFields()])
        self.assertFalse(index_def['index'] in t.getIndexes(1))
        self.assertFalse(index_def['index'] in t.getIndexDisplay(True).keys())
        self.assertTrue(index_def['friendlyName'] not in t.getIndexDisplay(True).values())
        # Make sure it's still in the un-limited list
        self.assertTrue(index_def['index'] in t.getIndexDisplay(False).keys())
        self.assertTrue(index_def['friendlyName'] in t.getIndexDisplay(False).values())
        self.assertTrue(index_def['index'] in t.getIndexes())

    def test_add_bogus_index(self):
        # You can add metadata that's not in the catalog
        t = self.tool
        t.addIndex('bogosity', enabled=True)
        self.assertTrue(t.getIndex('bogosity'))

        #Add
        t.addIndex('bogosity', enabled=True)
        self.assertTrue('bogosity' in [a[0] for a in t.getEnabledFields()])
        #Add
        t.addIndex('bogosity', enabled=True)
        self.assertTrue('bogosity' in t.getIndexDisplay(True).keys())
        #Add
        t.addIndex('bogosity', enabled=True)
        self.assertTrue('bogosity' in t.getIndexes(1))
        #Add
        t.addIndex('bogosity', enabled=True)
        self.assertTrue('bogosity' in [i.index for i in t.getEnabledIndexes()])

    def test_remove_index(self):
        t = self.tool
        t.addIndex(**index_def)
        t.removeIndex(index_def['index'])
        error = None
        try:
            index = t.topic_indexes[index_def['index']]
        except KeyError:
            error = True
        self.assertTrue(error)

        error = True
        try:
            index = t.getIndex(index_def['index'])
        except AttributeError:
            error = False
        self.assertFalse(error)

    def test_update_index(self):
        # An index with no criteria set should set all available criteria,
        # also changes made using updateIndex should not reset already set
        # values
        t = self.tool
        t.addIndex(enabled=True, **index_def)
        t.updateIndex(index_def['index'], criteria=None,
                      description='New Description')
        index = t.getIndex(index_def['index'])
        self.assertTrue(index.criteria)
        self.assertTrue(index.criteria != index_def['criteria'])
        self.assertTrue(index.description == 'New Description')
        self.assertTrue(index.friendlyName == index_def['friendlyName'])
        self.assertTrue(index.enabled)

    def test_all_indexes(self):
        # Ensure that the tool includes all indexes in the catalog
        t = self.tool
        cat = getToolByName(self.tool, 'portal_catalog')
        indexes = [field for field in cat.indexes()]
        init_indexes = list(t.getIndexes())
        unique_indexes = [i for i in indexes if i not in init_indexes]
        unique_indexes = unique_indexes + [i for i in init_indexes if i not in indexes]
        self.assertFalse(unique_indexes)

    def test_change_catalog_index(self):
        t = self.tool
        cat = getToolByName(self.tool, 'portal_catalog')
        #add
        error = True
        cat.manage_addIndex('nonsense', 'FieldIndex')
        try:
            t.getIndex('nonsense')
        except AttributeError:
            error = False
        self.assertFalse(error)
        #remove
        error = False
        cat.delIndex('nonsense')
        try:
            t.getIndex('nonsense')
        except AttributeError:
            error = True
        self.assertTrue(error)

    #Metadata tests
    def test_add_metadata(self):
        t = self.tool
        t.addMetadata(enabled=True, **meta_def)
        meta = t.getMetadata(meta_def['metadata'])
        self.assertEqual(meta.index, meta_def['metadata'])
        self.assertEqual(meta.friendlyName, meta_def['friendlyName'])
        self.assertEqual(meta.description, meta_def['description'])
        # Only need to test truth not actual value
        self.assertTrue(meta.enabled)

        self.assertTrue(meta in t.getEnabledMetadata())
        self.assertTrue(meta_def['metadata'] in t.getMetadataDisplay(True).keys())
        self.assertTrue(meta_def['friendlyName'] in t.getMetadataDisplay(True).values())
        self.assertTrue(meta_def['metadata'] in t.getAllMetadata(1))

    def test_disable_metadata(self):
        t = self.tool
        t.addMetadata(enabled=False, **meta_def)
        meta = t.getMetadata(meta_def['metadata'])
        self.assertEqual(meta.index, meta_def['metadata'])
        self.assertEqual(meta.friendlyName, meta_def['friendlyName'])
        self.assertEqual(meta.description, meta_def['description'])
        # Only need to test truth not actual value
        self.assertFalse(meta.enabled)

        self.assertTrue(meta not in t.getEnabledMetadata())
        self.assertFalse(meta_def['metadata'] in t.getAllMetadata(1))
        self.assertFalse(meta_def['metadata'] in t.getMetadataDisplay(True).keys())
        self.assertFalse(meta_def['friendlyName'] in t.getMetadataDisplay(True).values())
        # Make sure it's still in the un-limited list
        self.assertTrue(meta_def['metadata'] in t.getMetadataDisplay(False).keys())
        self.assertTrue(meta_def['friendlyName'] in t.getMetadataDisplay(False).values())
        self.assertTrue(meta_def['metadata'] in t.getAllMetadata())

    def test_add_bogus_metadata(self):
        # You can add metdata that's not in the catalog
        t = self.tool
        t.addMetadata('bogosity', enabled=True)
        self.assertTrue(t.getMetadata('bogosity'))

        #Add
        t.addMetadata('bogosity', enabled=True)
        self.assertTrue('bogosity' in t.getMetadataDisplay(True).keys())
        #Add
        t.addMetadata('bogosity', enabled=True)
        self.assertTrue('bogosity' in t.getAllMetadata(1))
        #Add
        t.addMetadata('bogosity', enabled=True)
        self.assertTrue('bogosity' in [i.index for i in t.getEnabledMetadata()])

    def test_remove_metadata(self):
        t = self.tool
        t.addMetadata(**meta_def)
        t.removeMetadata(meta_def['metadata'])
        error = None
        try:
            meta = t.topic_metadata[meta_def['metadata']]
        except KeyError:
            error = True
        self.assertTrue(error)

        error = True
        try:
            meta = t.getMetadata(meta_def['metadata'])
        except AttributeError:
            error = False
        self.assertFalse(error)

    def test_update_metadata(self):
        # Changes made using updateMetadata should not reset already set
        # values
        t = self.tool
        t.addMetadata(enabled=True, **meta_def)
        t.updateMetadata(meta_def['metadata'], friendlyName='New Name')
        meta = t.getMetadata(meta_def['metadata'])
        self.assertTrue(meta.friendlyName == 'New Name')
        self.assertTrue(meta.enabled)

    def test_all_metadata(self):
        # Ensure that the tool includes all metadata in the catalog
        t = self.tool
        cat = getToolByName(self.tool, 'portal_catalog')
        metadata = [field for field in cat.schema()]
        init_metadata = list(t.getAllMetadata())
        unique_metadata = [i for i in metadata if i not in init_metadata]
        unique_metadata = unique_metadata + [i for i in init_metadata if i not in metadata]
        self.assertFalse(unique_metadata)

    def test_change_catalog_schema(self):
        t = self.tool
        cat = getToolByName(self.tool, 'portal_catalog')
        #add
        error = True
        cat.manage_addColumn('nonsense')
        try:
            t.getMetadata('nonsense')
        except AttributeError:
            error = False
        self.assertFalse(error)
        #remove
        error = False
        cat.delColumn('nonsense')
        try:
            t.getMetadata('nonsense')
        except AttributeError:
            error = True
        self.assertTrue(error)

tests.append(TestTool)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
