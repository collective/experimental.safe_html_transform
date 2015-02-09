from unittest import TestCase, defaultTestLoader
from transaction import savepoint
from Acquisition import Implicit
from Testing.ZopeTestCase import ZopeTestCase
from zope.interface import implements
from plone.folder.interfaces import IOrderable
from plone.folder.ordered import OrderedBTreeFolderBase
from plone.folder.partial import PartialOrdering
from plone.folder.tests.utils import Orderable, Chaoticle
from plone.folder.tests.layer import PloneFolderLayer


class PartialOrderingTests(TestCase):
    """ tests regarding order-support for only items marked orderable """

    layer = PloneFolderLayer

    def create(self):
        container = OrderedBTreeFolderBase()
        container.setOrdering(u'partial')
        container['o1'] = Orderable('o1', 'mt1')
        container['o2'] = Orderable('o2', 'mt2')
        container['c1'] = Chaoticle('c1', 'mt3')
        container['o3'] = Orderable('o3', 'mt1')
        container['c2'] = Chaoticle('c2', 'mt2')
        container['c3'] = Chaoticle('c3', 'mt1')
        container['o4'] = Orderable('o4', 'mt2')
        self.unordered = ['c3', 'c2', 'c1']
        ordering = container.getOrdering()
        return container, ordering

    def testAdapter(self):
        container, ordering = self.create()
        self.failUnless(isinstance(ordering, PartialOrdering))

    def testNotifyAdded(self):
        container, ordering = self.create()
        self.assertEqual(ordering.idsInOrder(),
            ['o1', 'o2', 'o3', 'o4'] + self.unordered)
        container['o5'] = Orderable('o5')
        self.assertEqual(ordering.idsInOrder(),
            ['o1', 'o2', 'o3', 'o4', 'o5'] + self.unordered)
        self.assertEqual(set(container.objectIds()),
            set(['o1', 'o2', 'o3', 'o4', 'o5', 'c1', 'c2', 'c3']))

    def testNotifyRemoved(self):
        container, ordering = self.create()
        self.assertEqual(ordering.idsInOrder(),
            ['o1', 'o2', 'o3', 'o4'] + self.unordered)
        container._delOb('o3')
        self.assertEqual(ordering.idsInOrder(),
            ['o1', 'o2', 'o4'] + self.unordered)
        self.assertEqual(set(container.objectIds()),
            set(['o1', 'o2', 'o4', 'c1', 'c2', 'c3']))
        container._delOb('o1')
        self.assertEqual(ordering.idsInOrder(),
            ['o2', 'o4'] + self.unordered)
        self.assertEqual(set(container.objectIds()),
            set(['o2', 'o4', 'c1', 'c2', 'c3']))

    def runTableTests(self, action, tests):
        for args, order, rval in tests:
            container, ordering = self.create()
            ids = set(container.objectIds())
            method = getattr(ordering, action)
            if type(rval) == type(Exception):
                self.assertRaises(rval, method, *args)
            else:
                self.assertEqual(method(*args), rval)
            self.assertEqual(ordering.idsInOrder(), order + self.unordered)
            self.assertEqual(set(container.objectIds()), ids)   # all here?

    def testMoveObjectsByDelta(self):
        self.runTableTests('moveObjectsByDelta', (
            (('o1', 1),                                   ['o2', 'o1', 'o3', 'o4'], 1),
            (('o1', 2),                                   ['o2', 'o3', 'o1', 'o4'], 1),
            ((('o2', 'o4'), 1),                           ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o2', 'o4'), 9),                           ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o2', 'o3'), 1),                           ['o1', 'o4', 'o2', 'o3'], 2),
            ((('o2', 'o3'), 1, ('o1', 'o2', 'o3', 'o4')), ['o1', 'o4', 'o2', 'o3'], 2),
            ((('o2', 'o3'), 1, ('o1', 'o2', 'o3')),       ['o1', 'o2', 'o3', 'o4'], 0),
            ((('c1', 'o1'), 2),                           ['o2', 'o3', 'o1', 'o4'], 1),
            ((('c1', 'o3'), 1),                           ['o1', 'o2', 'o4', 'o3'], 1),
            ((('n2', 'o2'), 1),                           ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o4', 'o2'), 1),                           ['o1', 'o3', 'o2', 'o4'], 1),
        ))

    def testMoveObjectsDown(self):
        self.runTableTests('moveObjectsDown', (
            (('o1',),                                     ['o2', 'o1', 'o3', 'o4'], 1),
            (('o1', 2),                                   ['o2', 'o3', 'o1', 'o4'], 1),
            ((('o2', 'o4'),),                             ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o2', 'o4'), 9),                           ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o2', 'o3'),),                             ['o1', 'o4', 'o2', 'o3'], 2),
            ((('o2', 'o3'), 1, ('o1', 'o2', 'o3', 'o4')), ['o1', 'o4', 'o2', 'o3'], 2),
            ((('o2', 'o3'), 1, ('o1', 'o2', 'o3')),       ['o1', 'o2', 'o3', 'o4'], 0),
            ((('c1', 'o1'), 2),                           ['o2', 'o3', 'o1', 'o4'], 1),
            ((('c1', 'o3'),),                             ['o1', 'o2', 'o4', 'o3'], 1),
            ((('n2', 'o2'),),                             ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o4', 'o2'),),                             ['o1', 'o3', 'o2', 'o4'], 1),
        ))

    def testMoveObjectsUp(self):
        self.runTableTests('moveObjectsUp', (
            (('o4',),                                     ['o1', 'o2', 'o4', 'o3'], 1),
            (('o4', 1),                                   ['o1', 'o2', 'o4', 'o3'], 1),
            (('o4', 2),                                   ['o1', 'o4', 'o2', 'o3'], 1),
            ((('o1', 'o3'), 1),                           ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o1', 'o3'), 9),                           ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o2', 'o3'), 1),                           ['o2', 'o3', 'o1', 'o4'], 2),
            ((('o2', 'o3'), 1, ('o1', 'o2', 'o3', 'o4')), ['o2', 'o3', 'o1', 'o4'], 2),
            ((('o2', 'o3'), 1, ('o2', 'o3', 'o4')),       ['o1', 'o2', 'o3', 'o4'], 0),
            ((('c1', 'o4'), 2),                           ['o1', 'o4', 'o2', 'o3'], 1),
            ((('c1', 'o3'),),                             ['o1', 'o3', 'o2', 'o4'], 1),
            ((('n2', 'o3'), 1),                           ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o3', 'o1'), 1),                           ['o1', 'o3', 'o2', 'o4'], 1),
        ))

    def testMoveObjectsToTop(self):
        self.runTableTests('moveObjectsToTop', (
            (('o4',),                                  ['o4', 'o1', 'o2', 'o3'], 1),
            ((('o1', 'o3'),),                          ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o2', 'o3'),),                          ['o2', 'o3', 'o1', 'o4'], 2),
            ((('o2', 'o3'), ('o1', 'o2', 'o3', 'o4')), ['o2', 'o3', 'o1', 'o4'], 2),
            ((('o2', 'o3'), ('o2', 'o3', 'o4')),       ['o1', 'o2', 'o3', 'o4'], 0),
            ((('c1', 'o4'),),                          ['o4', 'o1', 'o2', 'o3'], 1),
            ((('c1', 'o3'),),                          ['o3', 'o1', 'o2', 'o4'], 1),
            ((('n2', 'o3'),),                          ['o3', 'o1', 'o2', 'o4'], 1),
            ((('o3', 'o1'),),                          ['o3', 'o1', 'o2', 'o4'], 1),
        ))

    def testMoveObjectsToBottom(self):
        self.runTableTests('moveObjectsToBottom', (
            (('o1',),                                  ['o2', 'o3', 'o4', 'o1'], 1),
            ((('o2', 'o4'),),                          ['o1', 'o3', 'o2', 'o4'], 1),
            ((('o2', 'o3'),),                          ['o1', 'o4', 'o2', 'o3'], 2),
            ((('o2', 'o3'), ('o1', 'o2', 'o3', 'o4')), ['o1', 'o4', 'o2', 'o3'], 2),
            ((('o2', 'o3'), ('o1', 'o2', 'o3')),       ['o1', 'o2', 'o3', 'o4'], 0),
            ((('c1', 'o1'),),                          ['o2', 'o3', 'o4', 'o1'], 1),
            ((('c1', 'o2'),),                          ['o1', 'o3', 'o4', 'o2'], 1),
            ((('n2', 'o3'),),                          ['o1', 'o2', 'o4', 'o3'], 1),
            ((('o4', 'o2'),),                          ['o1', 'o3', 'o4', 'o2'], 1),
        ))

    def testMoveObjectToPosition(self):
        self.runTableTests('moveObjectToPosition', (
            (('o2', 2), ['o1', 'o3', 'o2', 'o4'], 1),
            (('o4', 2), ['o1', 'o2', 'o4', 'o3'], 1),
            (('c1', 2), ['o1', 'o2', 'o3', 'o4'], None),    # existent, but non-orderable
            (('n2', 2), ['o1', 'o2', 'o3', 'o4'], ValueError),
        ))

    def testOrderObjects(self):
        self.runTableTests('orderObjects', (
            (('id', 'id'),       ['o4', 'o3', 'o2', 'o1'], -1),
            (('meta_type', ''),  ['o1', 'o3', 'o2', 'o4'], -1),
            # for the next line the sort order is different from the
            # original test in OFS, since the current implementation
            # keeps the original order as much as possible, i.e. minimize
            # exchange operations within the list;  this is correct as
            # far as the test goes, since it didn't specify a secondary
            # sort key...
            (('meta_type', 'n'), ['o2', 'o4', 'o1', 'o3'], -1),
        ))

    def testGetObjectPosition(self):
        self.runTableTests('getObjectPosition', (
            (('o2',), ['o1', 'o2', 'o3', 'o4'], 1),
            (('o4',), ['o1', 'o2', 'o3', 'o4'], 3),
            (('n2',), ['o1', 'o2', 'o3', 'o4'], ValueError),
            (('c2',), ['o1', 'o2', 'o3', 'o4'], None),      # existent, but non-orderable
        ))


class DummyFolder(OrderedBTreeFolderBase, Implicit):
    """ we need to mix in acquisition """
    implements(IOrderable)

    meta_type = 'DummyFolder'
    _ordering = u'partial'

    def dummy_method(self):
        return self.id


class PartialOrderingIntegrationTests(ZopeTestCase):

    layer = PloneFolderLayer

    def afterSetUp(self):
        context = self.app
        context._setOb('foo', DummyFolder('foo'))   # not pythonic in 2.10 :(
        context.foo['bar1'] = DummyFolder('bar1')
        context.foo['bar2'] = DummyFolder('bar2')
        context.foo['bar3'] = DummyFolder('bar3')
        savepoint(optimistic=True)
        self.assertEqual(self.registered, [])

    @property
    def registered(self):
        return self.app._p_jar._registered_objects

    def testAddObjectChangesOrderInfo(self):
        foo = self.app.foo
        foo['bar23'] = DummyFolder('bar23')
        self.assertEqual(foo.objectIds(), ['bar1', 'bar2', 'bar3', 'bar23'])
        self.failUnless(foo in self.registered, 'not registered?')

    def testRemoveObjectChangesOrderInfo(self):
        foo = self.app.foo
        foo._delOb('bar2',)
        self.assertEqual(foo.objectIds(), ['bar1', 'bar3'])
        self.failUnless(foo in self.registered, 'not registered?')

    def testMoveObjectChangesOrderInfo(self):
        foo = self.app.foo
        foo.moveObjectsUp(('bar2',))
        self.assertEqual(foo.objectIds(), ['bar2', 'bar1', 'bar3'])
        self.failUnless(foo in self.registered, 'not registered?')

    def testOrderObjectsChangesOrderInfo(self):
        foo = self.app.foo
        foo.orderObjects('id', reverse=True)
        self.assertEqual(foo.objectIds(), ['bar3', 'bar2', 'bar1'])
        self.failUnless(foo in self.registered, 'not registered?')
        # Reverse the current ordering.
        foo.orderObjects(reverse=True)
        self.assertEqual(foo.objectIds(), ['bar1', 'bar2', 'bar3'])

    def testOrderObjectsByMethodChangesOrderInfo(self):
        foo = self.app.foo
        foo.orderObjects('dummy_method', reverse=True)
        self.assertEqual(foo.objectIds(), ['bar3', 'bar2', 'bar1'])
        self.failUnless(foo in self.registered, 'not registered?')
        # Reverse the current ordering.
        foo.orderObjects(reverse=True)
        self.assertEqual(foo.objectIds(), ['bar1', 'bar2', 'bar3'])


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
