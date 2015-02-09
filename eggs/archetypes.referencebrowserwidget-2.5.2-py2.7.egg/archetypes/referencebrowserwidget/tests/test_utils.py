import unittest

from archetypes.referencebrowserwidget import utils
from archetypes.referencebrowserwidget.tests.base import TestCase
from Products.Archetypes.tests.utils import makeContent


class UtilsTestCase(unittest.TestCase):

    def test_emptyquotequery(self):
        assert utils.quotequery('') == ''
        assert utils.quotequery(None) is None

    def test_quotequery(self):
        assert utils.quotequery('foo and bar') == 'foo and bar'

    def test_quotequery_quote(self):
        assert utils.quotequery('foo and') == 'foo "and"'
        assert utils.quotequery('or bar') == '"or" bar'
        assert utils.quotequery('foo and or bar') == 'foo and "or" bar'


class PloneUtilsTestCase(TestCase):

    def afterSetUp(self):
        self.folder = self.createDefaultStructure()
        makeContent(self.folder, portal_type='Document', id='doc1')
        makeContent(self.folder, portal_type='Folder', id='folder1')
        makeContent(self.folder, portal_type='Folder', id='folder2')
        makeContent(self.folder.folder1, portal_type='Folder', id='subfolder1')
        makeContent(self.folder.folder1.subfolder1,
                    portal_type='Document', id='doc2')
        self.doc1 = self.folder.doc1
        self.doc2 = self.folder.folder1.subfolder1.doc2

    def beforeTearDown(self):
        self.removeDefaultStructure()

    def test_emptystartupdir(self):
        self.assertEqual(
            utils.getStartupDirectory(self.doc1, ''),
            'http://nohost/plone/layer1/layer2/doc1')

    def test_absstartupdir(self):
        self.assertEqual(
            utils.getStartupDirectory(self.doc1, '/rootfolder'),
            'http://nohost/plone/rootfolder')

    def test_relstartupdir(self):
        self.assertEqual(
            utils.getStartupDirectory(self.doc2, '../../folder2'),
            'http://nohost/plone/layer1/layer2/folder2')

        self.assertEqual(
            utils.getStartupDirectory(self.doc2, '..'),
            'http://nohost/plone/layer1/layer2/folder1/subfolder1')

        self.assertEqual(
            utils.getStartupDirectory(self.doc2, '../..'),
            'http://nohost/plone/layer1/layer2/folder1')


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
