from unittest import TestCase, defaultTestLoader

from Acquisition import aq_base
from plone.folder.ordered import OrderedBTreeFolderBase
from plone.folder.tests.layer import PloneFolderLayer
from plone.folder.tests.utils import DummyObject


class DictInterfaceTests(TestCase):
    """ tests for dict style interface """

    layer = PloneFolderLayer

    def test_getitem(self):
        folder = OrderedBTreeFolderBase("f1")
        foo = DummyObject('foo')
        folder._setOb('foo', foo)
        self.assertEqual(folder['foo'], foo)
        self.assertEqual(folder.__getitem__('foo'), foo)
        self.assertRaises(KeyError, folder.__getitem__, 'bar')

    def test_setitem(self):
        folder = OrderedBTreeFolderBase("f1")
        foo = DummyObject('foo')
        folder['foo'] = foo
        self.assertEqual(folder._getOb('foo'), foo)

    def test_contains(self):
        folder = OrderedBTreeFolderBase("f1")
        folder._setOb('foo', DummyObject('foo'))
        folder._setOb('bar', DummyObject('bar'))
        self.failUnless('foo' in folder)
        self.failUnless('bar' in folder)

    def test_delitem(self):
        folder = OrderedBTreeFolderBase("f1")
        folder._setOb('foo', DummyObject('foo'))
        folder._setOb('bar', DummyObject('bar'))
        self.assertEquals(len(folder.objectIds()), 2)
        del folder['foo']
        del folder['bar']
        self.assertEquals(len(folder.objectIds()), 0)

    def test_len_empty_folder(self):
        folder = OrderedBTreeFolderBase("f1")
        self.assertEquals(len(folder), 0)

    def test_len_one_child(self):
        folder = OrderedBTreeFolderBase("f1")
        folder['child'] = DummyObject('child')
        self.assertEquals(len(folder), 1)

    def test_to_verify_ticket_9120(self):
        folder = OrderedBTreeFolderBase("f1")
        folder['ob1'] = ob1 = DummyObject('ob1')
        folder['ob2'] = ob2 = DummyObject('ob2')
        folder['ob3'] = ob3 = DummyObject('ob3')
        folder['ob4'] = ob4 = DummyObject('ob4')
        del folder['ob2']
        del folder['ob3']
        self.assertEquals(folder.keys(), ['ob1', 'ob4'])
        self.assertEquals(map(aq_base, folder.values()), [ob1, ob4])
        self.assertEquals([key in folder for key in folder], [True, True])


class RelatedToDictInterfaceTests(TestCase):
    """ various tests which are related to the dict-like interface """

    layer = PloneFolderLayer

    def create(self):
        folder = OrderedBTreeFolderBase("f1")
        folder._setOb('o1', DummyObject('o1', 'mt1'))
        folder._setOb('o2', DummyObject('o2', 'mt2'))
        folder._setOb('o3', DummyObject('o3', 'mt1'))
        folder._setOb('o4', DummyObject('o4', 'mt2'))
        return folder

    def testObjectIdsWithSpec(self):
        folder = self.create()
        self.assertEquals(['o1', 'o3'], folder.objectIds(spec='mt1'))
        self.assertEquals(['o2', 'o4'], folder.objectIds(spec='mt2'))
        folder.moveObjectsToTop(['o3'])
        folder.moveObjectsDown(['o2'])
        self.assertEquals(['o3', 'o1'], folder.objectIds(spec='mt1'))
        self.assertEquals(['o4', 'o2'], folder.objectIds(spec='mt2'))


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
