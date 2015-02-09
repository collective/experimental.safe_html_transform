# simple benchmarking tests related to plip191
# to run individual tests using:
# $ bin/test -s plone.app.folder --tests-pattern=benchmarks -t <testName>
# where <testName> is something like "testObjectValuesOrdered"

from unittest import defaultTestLoader, main
from profilehooks import timecall
from random import randint

from transaction import commit
from Testing import ZopeTestCase as ztc

from Products.PloneTestCase import PloneTestCase as ptc
from Products.CMFPlone.utils import _createObjectByType
from Products.CMFPlone.PloneBatch import Batch
from plone.app.folder.tests.layer import IntegrationLayer
from plone.app.folder.tests.content import create as createNonBTreeFolder

# setup plone site
ptc.setupPloneSite()

# number of objects to create
SIZE = 500


class TestBenchmarkCase(ptc.PloneTestCase):

    class layer(IntegrationLayer):

        @classmethod
        def setUp(cls):
            app = ztc.app()
            portal = app.plone

            def create(container, nr):
                obj = _createObjectByType('Document', container, 'doc.%d' % nr)
                obj.setTitle('Title for %d' % nr)
                obj.setDescription('A long description for %d' % nr)
                obj.setText('This is the <b>HTML</b> text for item with id %d' % nr)
                obj.reindexObject(idxs=('Title', 'Description', 'SearchableText'))

            regular = createNonBTreeFolder('Folder', portal, 'regular')
            unordered = _createObjectByType('Folder', portal, 'unordered')
            unordered.setOrdering(u'unordered')
            ordered = _createObjectByType('Folder', portal, 'ordered')

            @timecall
            def testCreateContentRegular():
                for x in range(SIZE):
                    create(regular, x)
            @timecall
            def testCreateContentUnordered():
                for x in range(SIZE):
                    create(unordered, x)
            @timecall
            def testCreateContentOrdered():
                for x in range(SIZE):
                    create(ordered, x)

            testCreateContentRegular()
            testCreateContentUnordered()
            testCreateContentOrdered()

            commit()
            ztc.close(app)

        @classmethod
        def tearDown(cls):
            pass

    def afterSetUp(self):
        self.regular = self.portal.regular
        self.unordered = self.portal.unordered
        self.ordered = self.portal.ordered


    # basic content ids
    @timecall
    def testObjectIDsRegular(self):
        for x in range(5000):
            [i for i in self.regular.objectIds()]
    @timecall
    def testObjectIDsUnordered(self):
        for x in range(5000):
            [i for i in self.unordered.objectIds()]
    @timecall
    def testObjectIDsOrdered(self):
        for x in range(5000):
            [i for i in self.ordered.objectIds()]

    # basic content values -- read all
    @timecall
    def testObjectValuesRegular(self):
        for x in range(500):
            [obj for obj in self.regular.objectValues()]
    @timecall
    def testObjectValuesUnordered(self):
        for x in range(500):
            [obj for obj in self.unordered.objectValues()]
    @timecall
    def testObjectValuesOrdered(self):
        for x in range(500):
            [obj for obj in self.ordered.objectValues()]

    # object positions
    @timecall
    def testObjectPositionRegular(self):
        id = 'doc.%d' % (SIZE / 2)
        for x in range(100 ** 2):
            self.regular.getObjectPosition(id)
    @timecall
    def testObjectPositionUnordered(self):
        id = 'doc.%d' % (SIZE / 2)
        for x in range(100 ** 2):
            self.unordered.getObjectPosition(id)
    @timecall
    def testObjectPositionOrdered(self):
        id = 'doc.%d' % (SIZE / 2)
        for x in range(100 ** 2):
            self.ordered.getObjectPosition(id)

    # batching
    @timecall
    def testBatchRegular(self):
        for x in range(500):
            batch = Batch(sequence=self.regular.objectValues(), size=SIZE / 10, start=SIZE * 4 / 5)
            [b for b in batch]
    @timecall
    def testBatchUnordered(self):
        for x in range(500):
            batch = Batch(sequence=self.unordered.objectValues(), size=SIZE / 10, start=SIZE * 4 / 5)
            [b for b in batch]
    @timecall
    def testBatchOrdered(self):
        for x in range(500):
            batch = Batch(sequence=self.ordered.objectValues(), size=SIZE / 10, start=SIZE * 4 / 5)
            [b for b in batch]

    # random access
    @timecall
    def testRandomRegular(self):
        for x in range(1000):
            self.regular['doc.%d' % randint(0, SIZE-1)]
    @timecall
    def testRandomUnordered(self):
        for x in range(1000):
            self.unordered['doc.%d' % randint(0, SIZE-1)]
    @timecall
    def testRandomOrdered(self):
        for x in range(1000):
            self.ordered['doc.%d' % randint(0, SIZE-1)]


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    main(defaultTest='test_suite')
