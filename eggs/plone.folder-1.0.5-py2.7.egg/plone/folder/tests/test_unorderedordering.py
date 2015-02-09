from unittest import TestCase, defaultTestLoader
from plone.folder.ordered import OrderedBTreeFolderBase
from plone.folder.unordered import UnorderedOrdering
from plone.folder.tests.utils import DummyObject
from plone.folder.tests.layer import PloneFolderLayer


class UnorderedOrderingTests(TestCase):
    """ tests regarding order-support for folders with unordered ordering """

    layer = PloneFolderLayer

    def create(self):
        container = OrderedBTreeFolderBase()
        container._ordering = u'unordered'
        container._setOb('o1', DummyObject('o1', 'mt1'))
        container._setOb('o2', DummyObject('o2', 'mt2'))
        container._setOb('o3', DummyObject('o3', 'mt1'))
        container._setOb('o4', DummyObject('o4', 'mt2'))
        return container

    def testAdapter(self):
        container = self.create()
        ordering = container.getOrdering()
        self.failUnless(isinstance(ordering, UnorderedOrdering))

    def testNotifyAdded(self):
        container = self.create()
        self.assertEqual(set(container.objectIds()),
            set(['o1', 'o2', 'o3', 'o4']))
        container._setOb('o5', DummyObject('o5', 'mt1'))
        self.assertEqual(set(container.objectIds()),
            set(['o1', 'o2', 'o3', 'o4', 'o5']))

    def testNotifyRemoved(self):
        container = self.create()
        self.assertEqual(set(container.objectIds()),
            set(['o1', 'o2', 'o3', 'o4']))
        container._delOb('o3')
        self.assertEqual(set(container.objectIds()),
            set(['o1', 'o2', 'o4']))

    def testGetObjectPosition(self):
        container = self.create()
        self.assertEqual(container.getObjectPosition('o2'), None)


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
