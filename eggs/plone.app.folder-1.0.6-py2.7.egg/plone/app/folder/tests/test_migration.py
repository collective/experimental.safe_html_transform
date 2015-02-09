import re

from Acquisition import aq_base, aq_parent
from zope.interface import classImplements
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2Base as BTreeFolder
from Products.ATContentTypes.content.document import ATDocument
from Products.CMFPlone.utils import _createObjectByType
from plone.folder.interfaces import IOrderable, IOrdering
from plone.app.folder.tests.base import IntegrationTestCase
from plone.app.folder.tests.layer import IntegrationLayer
from plone.app.folder.tests.content import NonBTreeFolder, create
from plone.app.folder.tests.content import OrderableFolder
from plone.app.folder.migration import BTreeMigrationView
from plone.app.folder.utils import findObjects


def reverseMigrate(folder):
    """ helper to replace the given regular folder with one based on
        btrees;  the intention is to create the state that would be found
        before migration, i.e. a now btree-based folder still holding the
        data structures from a regular one;  all (regular) subfolders
        will be replaced recursively """
    for name, obj in reversed(list(findObjects(folder))):
        if isinstance(obj, NonBTreeFolder):
            parent = aq_parent(obj)
            data = obj.__dict__.copy()
            data['id'] = oid = obj.getId()
            new = OrderableFolder(oid)
            new.__dict__ = data
            setattr(parent, oid, new)


def isSaneBTreeFolder(folder):
    """ sanity-check the given btree folder """
    folder = aq_base(folder)
    contains = folder.__dict__.__contains__
    state = isinstance(folder, BTreeFolder) and contains('_tree') \
        and not contains('_objects')     # it's a class variable
    if state:
        try:
            # objects must not live directly on the folder (but in the btree)
            for oid in folder.objectIds():
                if not hasattr(folder, oid) or contains(oid):
                    return False
        except AttributeError:
            return False
    return state


def makeResponse(request):
    """ create a fake request and set up logging of output """
    headers = {}
    output = []
    class Response:
        def setHeader(self, header, value):
            headers[header] = value
        def write(self, msg):
            output.append(msg.strip())
    request.RESPONSE = Response()
    return headers, output, request


def getView(context, name, **kw):
    headers, output, request = makeResponse(TestRequest(**kw))
    view = getMultiAdapter((context, request), name=name)
    return view, headers, output, request


class TestMigrationHelpers(IntegrationTestCase):
    """ test helper functions for btree migration """

    layer = IntegrationLayer

    def testReverseMigrate(self):
        folder = create('Folder', self.portal, 'folder', title='Foo')
        create('Document', folder, 'doc1')
        create('Event', folder, 'event1')
        reverseMigrate(folder)
        btree = aq_base(self.portal.folder)
        self.failUnless(isinstance(btree, BTreeFolder))
        self.failUnless('_objects' in btree.__dict__)
        self.failUnless(hasattr(btree, '_tree'))
        self.failIf('_tree' in btree.__dict__)
        self.assertEqual(btree._tree, None)
        # please note that the default adapter returns empty lists here
        # while the partial one raises `AttributeErrors`
        try:
            self.assertEqual(list(btree.objectValues()), [])
            self.assertEqual(list(btree.objectIds()), [])
        except AttributeError:
            # BBB In Zope 2.13 this always raises AttributeError
            pass
        self.assertEqual(btree._objects,
            (dict(id='doc1', meta_type='ATDocument'),
            (dict(id='event1', meta_type='ATEvent'))))
        self.assertEqual(btree.getId(), 'folder')
        self.assertEqual(btree.Title(), 'Foo')

    def testNestedReverseMigrate(self):
        folder = create('Folder', self.portal, 'foo')
        create('Folder', folder, 'bar')
        reverseMigrate(folder)
        foo = aq_base(self.portal.foo)
        self.failUnless(isinstance(foo, BTreeFolder))
        self.failUnless('_objects' in foo.__dict__)
        self.failUnless(hasattr(foo, '_tree'))
        self.failIf('_tree' in foo.__dict__)
        self.assertEqual(foo._tree, None)
        self.assertEqual(foo._objects,
            (dict(id='bar', meta_type='NonBTreeFolder'), ))
        bar = aq_base(getattr(foo, 'bar'))
        self.failUnless(isinstance(bar, BTreeFolder))
        self.failIf('_objects' in bar.__dict__)   # no sub-objects
        self.assertEqual(bar._objects, ())
        self.failUnless(hasattr(bar, '_tree'))
        self.failIf('_tree' in bar.__dict__)
        self.assertEqual(bar._tree, None)
        self.assertEqual(bar._objects, ())

    def testIsSaneBTreeFolder(self):
        # positive case
        _createObjectByType('Folder', self.portal, 'btree')
        self.failUnless(isSaneBTreeFolder(self.portal.btree))
        # negative case
        create('Folder', self.portal, 'folder')
        self.failIf(isSaneBTreeFolder(self.portal.folder))
        reverseMigrate(self.portal.folder)
        self.failIf(isSaneBTreeFolder(self.portal.folder))


class TestBTreeMigration(IntegrationTestCase):
    """ test BTree migration tests migration between Folder and
        btree-based folder """

    layer = IntegrationLayer

    def afterSetUp(self):
        self.portal._delObject('news')
        self.portal._delObject('events')
        classImplements(ATDocument, IOrderable)

    def makeUnmigratedFolder(self, context, name, **kw):
        """ create a folder in an unmigrated state """
        folder = create('Folder', context, name, **kw)
        reverseMigrate(folder)
        self.failIf(isSaneBTreeFolder(folder))
        return context[name]

    def testBTreeMigration(self):
        # create (unmigrated) btree folder
        folder = self.makeUnmigratedFolder(self.portal, 'test', title='Foo')
        view = BTreeMigrationView(self.portal, self.app.REQUEST)
        self.failUnless(view.migrate(folder))
        folder = self.portal.test       # get the object again...
        self.failUnless(isSaneBTreeFolder(folder))
        self.assertEqual(folder.getId(), 'test')
        self.assertEqual(folder.Title(), 'Foo')
        # a second migration should be skipped
        self.failIf(view.migrate(folder))

    def getNumber(self, output):
        self.failUnless(len(output) >= 3)
        self.failUnless('migrating btree-based folders' in output[0])
        self.failUnless('intermediate commit' in output[-2])
        last = output[-1]
        self.failUnless('processed' in last)
        matches = re.match(r'.*processed (.*) object.*', last).groups()
        return int(matches[0])

    def testMigrationView(self):
        folder = self.makeUnmigratedFolder(self.portal, 'test', title='Foo')
        view, headers, output, request = getView(folder, 'migrate-btrees')
        view()      # call the view, triggering the migration
        num = self.getNumber(output)
        self.assertEqual(num, 1)
        folder = self.portal.test               # get the object again...
        self.failUnless(isSaneBTreeFolder(folder))
        self.assertEqual(folder.getId(), 'test')
        self.assertEqual(folder.Title(), 'Foo')

    def testMigrationViewWithSubobjects(self):
        # set up an (unmigrated) folder with subobjects
        folder = create('Folder', self.portal, 'test', title='Foo')
        create('Document', folder, 'doc1')
        create('Event', folder, 'event1')
        reverseMigrate(folder)
        folder = self.portal.test               # get the object again...
        self.failIf(isSaneBTreeFolder(folder))
        # now test its migration...
        view, headers, output, request = getView(self.portal, 'migrate-btrees')
        view()      # call the view, triggering the migration
        num = self.getNumber(output)
        self.assertEqual(num, 1)
        folder = self.portal.test               # get the object again...
        self.failUnless(isSaneBTreeFolder(folder))
        self.assertEqual(folder.getId(), 'test')
        self.assertEqual(folder.Title(), 'Foo')
        self.assertEqual(len(folder.objectValues()), 2)
        self.assertEqual(set(folder.objectIds()), set(['doc1', 'event1']))
        self.assertEqual(IOrdering(folder).idsInOrder(), ['doc1', 'event1'])

    def testMigrationViewForMultipleFolders(self):
        self.makeUnmigratedFolder(self.portal, 'folder1')
        self.makeUnmigratedFolder(self.portal, 'folder2')
        view, headers, output, request = getView(self.portal, 'migrate-btrees')
        view()      # call the view, triggering the migration
        num = self.getNumber(output)
        self.assertEqual(num, 2)
        self.failUnless(isSaneBTreeFolder(self.portal.folder1))
        self.failUnless(isSaneBTreeFolder(self.portal.folder2))

    def testMigrationViewForNestedFolders(self):
        # nested folders have to be "unmigrated" in bottom-up...
        folder = create('Folder', self.portal, 'test')
        create('Folder', self.portal.test, 'foo')
        create('Folder', self.portal.test, 'bar')
        reverseMigrate(folder)
        self.failIf(isSaneBTreeFolder(folder))
        # start the migration
        view, headers, output, request = getView(self.portal, 'migrate-btrees')
        view()      # call the view, triggering the migration
        num = self.getNumber(output)
        self.assertEqual(num, 3)
        self.failUnless(isSaneBTreeFolder(self.portal.test))
        self.failUnless(isSaneBTreeFolder(self.portal.test.foo))
        self.failUnless(isSaneBTreeFolder(self.portal.test.bar))


def test_suite():
    from unittest import defaultTestLoader
    return defaultTestLoader.loadTestsFromName(__name__)
