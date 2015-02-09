from unittest import defaultTestLoader, main
from Testing import ZopeTestCase as ztc
from plone.app.folder.utils import findObjects


class UtilsTests(ztc.ZopeTestCase):

    def afterSetUp(self):
        self.app.manage_addFolder(id='portal', title='Portal')
        self.portal = self.app.portal
        self.portal.manage_addFolder(id='foo', title='Foo')
        self.portal.foo.manage_addFolder(id='bar', title='Bar')
        self.portal.foo.bar.manage_addDocument(id='doc1', title='a document')
        self.portal.foo.bar.manage_addDocument(id='file1', title='a file')
        self.portal.manage_addFolder(id='bar', title='Bar')
        self.portal.bar.manage_addFolder(id='foo', title='Foo')
        self.portal.bar.foo.manage_addDocument(id='doc2', title='a document')
        self.portal.bar.foo.manage_addDocument(id='file2', title='a file')
        self.good = ('bar', 'bar/foo', 'bar/foo/doc2', 'bar/foo/file2',
            'foo', 'foo/bar', 'foo/bar/doc1', 'foo/bar/file1')

    def ids(self, results):
        return tuple(sorted([r[0] for r in results]))

    def testZopeFindAndApply(self):
        found = self.app.ZopeFindAndApply(self.portal, search_sub=True)
        self.assertEqual(self.ids(found), self.good)

    def testFindObjects(self):
        found = list(findObjects(self.portal))
        # the starting point itself is returned
        self.assertEqual(found[0], ('', self.portal))
        # but the rest should be the same...
        self.assertEqual(self.ids(found[1:]), self.good)


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    main(defaultTest='test_suite')
