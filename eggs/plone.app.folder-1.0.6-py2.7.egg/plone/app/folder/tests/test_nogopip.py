from unittest import defaultTestLoader
from plone.app.folder.tests.base import IntegrationTestCase
from plone.app.folder.tests.content import UnorderedFolder
from plone.app.folder.tests.layer import IntegrationLayer


class NoGopipTests(IntegrationTestCase):

    layer = IntegrationLayer

    def afterSetUp(self):
        self.setRoles(['Manager'])
        folder = self.portal[self.portal.invokeFactory('Folder', 'foo')]
        subfolder = folder[folder.invokeFactory('Folder', 'sub')]
        folder.invokeFactory('Document', id='bar2')
        folder.invokeFactory('Document', id='bar1')
        folder.invokeFactory('Document', id='bar3')
        folder.invokeFactory('Document', id='bar4')
        subfolder.invokeFactory('Document', id='bar5')

    def query(self, **kw):
        return [brain.getId for brain in self.portal.portal_catalog(
            sort_on='getObjPositionInParent', **kw)]

    def testSearchOneFolder(self):
        ids = self.query(path=dict(query='/plone/foo', depth=1))
        self.assertEqual(ids, ['sub', 'bar2', 'bar1', 'bar3', 'bar4'])

    def testSortDocumentsInFolder(self):
        ids = self.query(path=dict(query='/plone/foo', depth=1), Type='Page')
        self.assertEqual(ids, ['bar2', 'bar1', 'bar3', 'bar4'])

    def testSortDocumentsInTree(self):
        ids = self.query(path='/plone/foo', Type='Page')
        self.assertEqual(ids, ['bar5', 'bar2', 'bar1', 'bar3', 'bar4'])

    def testSearchUnorderedFolder(self):
        self.portal['foo1'] = UnorderedFolder('foo1')
        base = self.portal.foo1
        base.reindexObject(idxs=['path', 'getObjPositionInParent'])
        base.invokeFactory('Document', id='bar2')
        base.invokeFactory('Document', id='bar1')
        ids = self.query(path=dict(query='/plone/foo1', depth=1))
        self.assertEqual(ids, ['bar2', 'bar1'])

    def testSearchUnorderedFolderInFolder(self):
        self.portal['foo']['foo1'] = UnorderedFolder('foo1')
        base = self.portal.foo.foo1
        base.reindexObject(idxs=['path', 'getObjPositionInParent'])
        base.invokeFactory('Document', id='bar7')
        base.invokeFactory('Document', id='bar6')
        ids = self.query(path=dict(query='/plone/foo/foo1', depth=1))
        self.assertEqual(ids, ['bar7', 'bar6'])

    def testSortUnorderedFolderInTree(self):
        self.portal.foo['foo1'] = UnorderedFolder('foo1')
        base = self.portal.foo.foo1
        base.reindexObject(idxs=['path', 'getObjPositionInParent'])
        base.invokeFactory('Document', id='bar7')
        base.invokeFactory('Document', id='bar6')
        ids = self.query(path='/plone/foo', Type='Page')
        self.assertEqual(ids,
            ['bar5', 'bar7', 'bar6', 'bar2', 'bar1', 'bar3', 'bar4'])


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
