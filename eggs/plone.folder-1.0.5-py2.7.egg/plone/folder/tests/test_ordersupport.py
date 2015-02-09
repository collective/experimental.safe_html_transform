from unittest import TestCase, defaultTestLoader

from plone.folder.interfaces import IOrdering
from plone.folder.ordered import OrderedBTreeFolderBase
from plone.folder.tests.layer import PloneFolderLayer
from plone.folder.tests.utils import DummyObject


class OFSOrderSupportTests(TestCase):
    """ tests borrowed from OFS.tests.testOrderSupport """

    layer = PloneFolderLayer

    def create(self):
        folder = OrderedBTreeFolderBase('f1')
        folder['o1'] = DummyObject('o1', 'mt1')
        folder['o2'] = DummyObject('o2', 'mt2')
        folder['o3'] = DummyObject('o3', 'mt1')
        folder['o4'] = DummyObject('o4', 'mt2')
        return folder

    # Test for ordering of basic methods

    def test_objectIdsOrdered(self):
        folder = self.create()
        self.assertEquals(["o1", "o2", "o3", "o4"], folder.objectIds())
        folder.moveObjectsUp(("o2",), 1)
        self.assertEquals(["o2", "o1", "o3", "o4"], folder.objectIds())

    def test_objectValuesOrdered(self):
        folder = self.create()
        self.assertEquals(["o1", "o2", "o3", "o4"], [x.id for x in folder.objectValues()])
        folder.moveObjectsUp(("o2",), 1)
        self.assertEquals(["o2", "o1", "o3", "o4"], [x.id for x in folder.objectValues()])

    def test_objectItemsOrdered(self):
        folder = self.create()
        self.assertEquals(["o1", "o2", "o3", "o4"], [x for x, y in folder.objectItems()])
        folder.moveObjectsUp(("o2",), 1)
        self.assertEquals(["o2", "o1", "o3", "o4"], [x for x, y in folder.objectItems()])

    def test_iterkeys(self):
        folder = self.create()
        self.assertEquals(["o1", "o2", "o3", "o4"], [x for x in folder.iterkeys()])
        folder.moveObjectsUp(("o2",), 1)
        self.assertEquals(["o2", "o1", "o3", "o4"], [x for x in folder.iterkeys()])

    def test_iter(self):
        folder = self.create()
        self.assertEquals(["o1", "o2", "o3", "o4"], [x for x in folder])
        folder.moveObjectsUp(("o2",), 1)
        self.assertEquals(["o2", "o1", "o3", "o4"], [x for x in folder])

    def test_getitem(self):
        ordering = IOrdering(self.create())
        self.assertEquals(ordering[1], 'o2')
        self.assertEquals(ordering[-1], 'o4')
        self.assertEquals(ordering[1:2], ['o2'])
        self.assertEquals(ordering[1:-1], ['o2', 'o3'])
        self.assertEquals(ordering[1:], ['o2', 'o3', 'o4'])

    # Tests borrowed from OFS.tests.testsOrderSupport

    def runTableTests(self, methodname, table):
        for args, order, rval in table:
            f = self.create()
            method = getattr(f, methodname)
            if rval == 'ValueError':
                self.failUnlessRaises(ValueError, method, *args)
            else:
                self.failUnlessEqual(method(*args), rval)
            self.failUnlessEqual(f.objectIds(), order)

    def test_moveObjectsUp(self):
        self.runTableTests('moveObjectsUp',
              ( ( ( 'o4', 1 ),         ['o1', 'o2', 'o4', 'o3'], 1 )
              , ( ( 'o4', 2 ),         ['o1', 'o4', 'o2', 'o3'], 1 )
              , ( ( ('o1', 'o3'), 1 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o1', 'o3'), 9 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o2', 'o3'), 1 ), ['o2', 'o3', 'o1', 'o4'], 2 )
              , ( ( ('o2', 'o3'), 1, ('o1', 'o2', 'o3', 'o4') ),
                                       ['o2', 'o3', 'o1', 'o4'], 2 )
              , ( ( ('o2', 'o3'), 1, ('o2', 'o3', 'o4') ),
                                       ['o1', 'o2', 'o3', 'o4'], 0 )
              , ( ( ('n2', 'o3'), 1 ), ['o1', 'o3', 'o2', 'o4'], 1)
              , ( ( ('o3', 'o1'), 1 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              )
            )

    def test_moveObjectsDown(self):
        self.runTableTests('moveObjectsDown',
              ( ( ( 'o1', 1 ),         ['o2', 'o1', 'o3', 'o4'], 1 )
              , ( ( 'o1', 2 ),         ['o2', 'o3', 'o1', 'o4'], 1 )
              , ( ( ('o2', 'o4'), 1 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o2', 'o4'), 9 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o2', 'o3'), 1 ), ['o1', 'o4', 'o2', 'o3'], 2 )
              , ( ( ('o2', 'o3'), 1, ('o1', 'o2', 'o3', 'o4') ),
                                       ['o1', 'o4', 'o2', 'o3'], 2 )
              , ( ( ('o2', 'o3'), 1, ('o1', 'o2', 'o3') ),
                                       ['o1', 'o2', 'o3', 'o4'], 0 )
              , ( ( ('n2', 'o3'), 1 ), ['o1', 'o2', 'o4', 'o3'], 1)
              , ( ( ('o4', 'o2'), 1 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              )
            )

    def test_moveObjectsToTop(self):
        self.runTableTests('moveObjectsToTop',
              ( ( ( 'o4', ),         ['o4', 'o1', 'o2', 'o3'], 1 )
              , ( ( ('o1', 'o3'), ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o2', 'o3'), ), ['o2', 'o3', 'o1', 'o4'], 2 )
              , ( ( ('o2', 'o3'), ('o1', 'o2', 'o3', 'o4') ),
                                     ['o2', 'o3', 'o1', 'o4'], 2 )
              , ( ( ('o2', 'o3'), ('o2', 'o3', 'o4') ),
                                     ['o1', 'o2', 'o3', 'o4'], 0 )
              , ( ( ('n2', 'o3'), ), ['o3', 'o1', 'o2', 'o4'], 1)
              , ( ( ('o3', 'o1'), ), ['o3', 'o1', 'o2', 'o4'], 1 )
              )
            )

    def test_moveObjectsToBottom(self):
        self.runTableTests('moveObjectsToBottom',
              ( ( ( 'o1', ),         ['o2', 'o3', 'o4', 'o1'], 1 )
              , ( ( ('o2', 'o4'), ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o2', 'o3'), ), ['o1', 'o4', 'o2', 'o3'], 2 )
              , ( ( ('o2', 'o3'), ('o1', 'o2', 'o3', 'o4') ),
                                     ['o1', 'o4', 'o2', 'o3'], 2 )
              , ( ( ('o2', 'o3'), ('o1', 'o2', 'o3') ),
                                     ['o1', 'o2', 'o3', 'o4'], 0 )
              , ( ( ('n2', 'o3'), ), ['o1', 'o2', 'o4', 'o3'], 1)
              , ( ( ('o4', 'o2'), ), ['o1', 'o3', 'o4', 'o2'], 1 )
              )
            )

    def test_orderObjects(self):
        self.runTableTests('orderObjects',
              ( ( ( 'id', 'id' ),       ['o4', 'o3', 'o2', 'o1'], -1)
              , ( ( 'meta_type', '' ),  ['o1', 'o3', 'o2', 'o4'], -1)
              # for the next line the sort order is different from the
              # original test in OFS, since the current implementation
              # keeps the original order as much as possible, i.e. minimize
              # exchange operations within the list;  this is correct as
              # far as the test goes, since it didn't specify a secondary
              # sort key...
              , ( ( 'meta_type', 'n' ), ['o2', 'o4', 'o1', 'o3'], -1)
              )
            )

    def test_getObjectPosition(self):
        self.runTableTests('getObjectPosition',
              ( ( ( 'o2', ), ['o1', 'o2', 'o3', 'o4'], 1)
              , ( ( 'o4', ), ['o1', 'o2', 'o3', 'o4'], 3)
              , ( ( 'n2', ), ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              )
            )

    def test_moveObjectToPosition(self):
        self.runTableTests('moveObjectToPosition',
              ( ( ( 'o2', 2 ), ['o1', 'o3', 'o2', 'o4'], 1)
              , ( ( 'o4', 2 ), ['o1', 'o2', 'o4', 'o3'], 1)
              , ( ( 'n2', 2 ), ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              )
            )


class PloneOrderSupportTests(TestCase):
    """ tests borrowed from Products.CMFPlone.tests.testOrderSupport """

    layer = PloneFolderLayer

    def setUp(self):
        self.folder = OrderedBTreeFolderBase("f1")
        self.folder['foo'] = DummyObject('foo', 'mt1')
        self.folder['bar'] = DummyObject('bar', 'mt1')
        self.folder['baz'] = DummyObject('baz', 'mt1')

    def testGetObjectPosition(self):
        self.assertEqual(self.folder.getObjectPosition('foo'), 0)
        self.assertEqual(self.folder.getObjectPosition('bar'), 1)
        self.assertEqual(self.folder.getObjectPosition('baz'), 2)

    def testMoveObject(self):
        self.folder.moveObjectToPosition('foo', 1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 0)
        self.assertEqual(self.folder.getObjectPosition('foo'), 1)
        self.assertEqual(self.folder.getObjectPosition('baz'), 2)

    def testMoveObjectToSamePos(self):
        self.folder.moveObjectToPosition('bar', 1)
        self.assertEqual(self.folder.getObjectPosition('foo'), 0)
        self.assertEqual(self.folder.getObjectPosition('bar'), 1)
        self.assertEqual(self.folder.getObjectPosition('baz'), 2)

    def testMoveObjectToFirstPos(self):
        self.folder.moveObjectToPosition('bar', 0)
        self.assertEqual(self.folder.getObjectPosition('bar'), 0)
        self.assertEqual(self.folder.getObjectPosition('foo'), 1)
        self.assertEqual(self.folder.getObjectPosition('baz'), 2)

    def testMoveObjectToLastPos(self):
        self.folder.moveObjectToPosition('bar', 2)
        self.assertEqual(self.folder.getObjectPosition('foo'), 0)
        self.assertEqual(self.folder.getObjectPosition('baz'), 1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 2)

    def testMoveObjectOutLowerBounds(self):
        # Pos will be normalized to 0
        self.folder.moveObjectToPosition('bar', -1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 0)
        self.assertEqual(self.folder.getObjectPosition('foo'), 1)
        self.assertEqual(self.folder.getObjectPosition('baz'), 2)

    def testMoveObjectOutUpperBounds(self):
        # Pos will be normalized to 2
        self.folder.moveObjectToPosition('bar', 3)
        self.assertEqual(self.folder.getObjectPosition('foo'), 0)
        self.assertEqual(self.folder.getObjectPosition('baz'), 1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 2)

    def testMoveObjectsUp(self):
        self.folder.moveObjectsUp(['bar'])
        self.assertEqual(self.folder.getObjectPosition('bar'), 0)
        self.assertEqual(self.folder.getObjectPosition('foo'), 1)
        self.assertEqual(self.folder.getObjectPosition('baz'), 2)

    def testMoveObjectsDown(self):
        self.folder.moveObjectsDown(['bar'])
        self.assertEqual(self.folder.getObjectPosition('foo'), 0)
        self.assertEqual(self.folder.getObjectPosition('baz'), 1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 2)

    def testMoveObjectsToTop(self):
        self.folder.moveObjectsToTop(['bar'])
        self.assertEqual(self.folder.getObjectPosition('bar'), 0)
        self.assertEqual(self.folder.getObjectPosition('foo'), 1)
        self.assertEqual(self.folder.getObjectPosition('baz'), 2)

    def testMoveObjectsToBottom(self):
        self.folder.moveObjectsToBottom(['bar'])
        self.assertEqual(self.folder.getObjectPosition('foo'), 0)
        self.assertEqual(self.folder.getObjectPosition('baz'), 1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 2)

    def testMoveTwoObjectsUp(self):
        self.folder.moveObjectsUp(['bar', 'baz'])
        self.assertEqual(self.folder.getObjectPosition('bar'), 0)
        self.assertEqual(self.folder.getObjectPosition('baz'), 1)
        self.assertEqual(self.folder.getObjectPosition('foo'), 2)

    def testMoveTwoObjectsDown(self):
        self.folder.moveObjectsDown(['foo', 'bar'])
        self.assertEqual(self.folder.getObjectPosition('baz'), 0)
        self.assertEqual(self.folder.getObjectPosition('foo'), 1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 2)

    def testMoveTwoObjectsToTop(self):
        self.folder.moveObjectsToTop(['bar', 'baz'])
        self.assertEqual(self.folder.getObjectPosition('bar'), 0)
        self.assertEqual(self.folder.getObjectPosition('baz'), 1)
        self.assertEqual(self.folder.getObjectPosition('foo'), 2)

    def testMoveTwoObjectsToBottom(self):
        self.folder.moveObjectsToBottom(['foo', 'bar'])
        self.assertEqual(self.folder.getObjectPosition('baz'), 0)
        self.assertEqual(self.folder.getObjectPosition('foo'), 1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 2)

    def testOrderObjects(self):
        self.folder.orderObjects('id')
        self.assertEqual(self.folder.getObjectPosition('bar'), 0)
        self.assertEqual(self.folder.getObjectPosition('baz'), 1)
        self.assertEqual(self.folder.getObjectPosition('foo'), 2)

    def testOrderObjectsReverse(self):
        self.folder.orderObjects('id', reverse=True)
        self.assertEqual(self.folder.getObjectPosition('foo'), 0)
        self.assertEqual(self.folder.getObjectPosition('baz'), 1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 2)

    def testOrderObjectsByMethod(self):
        self.folder.orderObjects('dummy_method')
        self.assertEqual(self.folder.getObjectPosition('bar'), 0)
        self.assertEqual(self.folder.getObjectPosition('baz'), 1)
        self.assertEqual(self.folder.getObjectPosition('foo'), 2)

    def testOrderObjectsOnlyReverse(self):
        self.folder.orderObjects(reverse=True)
        self.assertEqual(self.folder.getObjectPosition('baz'), 0)
        self.assertEqual(self.folder.getObjectPosition('bar'), 1)
        self.assertEqual(self.folder.getObjectPosition('foo'), 2)

    def testSubsetIds(self):
        self.folder.moveObjectsByDelta(['baz'], -1, ['foo', 'bar', 'baz'])
        self.assertEqual(self.folder.getObjectPosition('foo'), 0)
        self.assertEqual(self.folder.getObjectPosition('baz'), 1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 2)

    def testSkipObjectsNotInSubsetIds(self):
        self.folder.moveObjectsByDelta(['baz'], -1, ['foo', 'baz'])
        self.assertEqual(self.folder.getObjectPosition('baz'), 0)
        self.assertEqual(self.folder.getObjectPosition('bar'), 1) # Did not move
        self.assertEqual(self.folder.getObjectPosition('foo'), 2)

    def testIgnoreNonObjects(self):
        # Fix for (http://dev.plone.org/plone/ticket/3959) non
        # contentish objects cause errors, we should just ignore them
        self.folder.moveObjectsByDelta(['bar','blah'], -1)
        self.assertEqual(self.folder.getObjectPosition('bar'), 0)
        self.assertEqual(self.folder.getObjectPosition('foo'), 1)
        self.assertEqual(self.folder.getObjectPosition('baz'), 2)


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
