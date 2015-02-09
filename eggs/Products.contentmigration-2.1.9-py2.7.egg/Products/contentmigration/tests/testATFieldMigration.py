from Products.contentmigration.tests.cmtc import ContentMigratorTestCase
from Products.contentmigration.tests.cmtc import makeUpper
from Products.contentmigration.tests.cmtc import conditionallyAbortAttribute
from Products.contentmigration.tests.cmtc import conditionallyAbortObject
from Products.contentmigration.tests.cmtc import callAfterAttribute
from Products.Archetypes.Storage.annotation import AnnotationStorage
from Products.Archetypes.Storage import AttributeStorage


class TestFieldMigration(ContentMigratorTestCase):
    """Test migration of in-instance AT fields"""

    def afterSetUp(self):
        # Create some content to migrate
        self.folder.invokeFactory('Document', 'd1')
        self.folder.invokeFactory('Document', 'd2')
        self.folder.invokeFactory('News Item', 'n1')
        self.folder.invokeFactory('News Item', 'n2')

        self.folder['d1'].setTitle('Document 1')
        self.folder['d1'].setDescription('Description 1')
        self.folder['d1'].setText('Body one')

        self.folder['d2'].setTitle('Document 2')
        self.folder['d2'].setDescription('Description 2')
        self.folder['d2'].setText('Body two')

        self.folder['n1'].setTitle('News 1')
        self.folder['n1'].setDescription('Description 3')
        self.folder['n1'].setText('News one')

        self.folder['n2'].setTitle('News 2')
        self.folder['n2'].setDescription('Description 4')
        self.folder['n2'].setText('News two')

        self.portal._delObject('front-page')

        self.setRoles(['Manager', 'Member'])

    def testAttributeRenaming(self):
        storage = AnnotationStorage()
        query   = {}
        actions = ({'fieldName'    : 'text',
                    'newFieldName' : 'bodyText',
                    'storage'      : storage
                    },)

        self.execute(query, actions)
        self.assertEqual(storage.get('bodyText', self.folder['d1']).getRaw(), 'Body one')
        self.assertEqual(storage.get('bodyText', self.folder['d2']).getRaw(), 'Body two')
        self.assertRaises(AttributeError, storage.get, 'text', self.folder['d1'])

    def testTransform(self):
        storage = AnnotationStorage()
        query   = {}
        actions = ({'fieldName'    : 'text',
                    'storage'      : storage,
                    'transform'    : makeUpper
                     },)
        self.execute(query, actions)
        self.assertEqual(storage.get('text', self.folder['d1']).getRaw(), 'BODY ONE')
        self.assertEqual(storage.get('text', self.folder['d2']).getRaw(), 'BODY TWO')

    def testAttributeRenamingAndTransform(self):
        storage = AnnotationStorage()
        query   = {}
        actions = ({'fieldName'    : 'text',
                    'newFieldName' : 'bodyText',
                    'storage'      : storage,
                    'transform'    : makeUpper
                     },)
        self.execute(query, actions)
        self.assertEqual(storage.get('bodyText', self.folder['d1']).getRaw(), 'BODY ONE')
        self.assertEqual(storage.get('bodyText', self.folder['d2']).getRaw(), 'BODY TWO')

    def testNewStorageAndAttribute(self):
        storage = AnnotationStorage()
        newStorage = AttributeStorage()
        query   = {}
        actions = ({'fieldName'    : 'text',
                    'newFieldName' : 'bodyText',
                    'storage'      : storage,
                    'newStorage'   : newStorage
                    },)
        self.execute(query, actions)
        self.assertEqual(getattr(self.folder['d1'], 'bodyText').getRaw(), 'Body one')
        self.assertEqual(getattr(self.folder['d2'], 'bodyText').getRaw(), 'Body two')
        self.assertRaises(AttributeError, storage.get, 'text', self.folder['d1'])

    def testNewStorageOnly(self):
        storage = AnnotationStorage()
        newStorage = AttributeStorage()
        query   = {}
        actions = ({'fieldName'    : 'text',
                    'storage'      : storage,
                    'newStorage'   : newStorage
                    },)
        self.execute(query, actions)
        self.assertEqual(getattr(self.folder['d1'], 'text').getRaw(), 'Body one')
        self.assertEqual(getattr(self.folder['d2'], 'text').getRaw(), 'Body two')

        try:
            storage.get('text', self.folder['d1'])
        except AttributeError:
            pass
        else:
            self.fail()

    def testAbortAttribute(self):
        storage = AnnotationStorage()
        query   = {}
        actions = ({'fieldName'    : 'text',
                    'transform'    : makeUpper,
                    'storage'      : storage,
                    'callBefore'   : conditionallyAbortAttribute,
                   },)
        self.execute(query, actions)
        self.assertEqual(storage.get('text', self.folder['d1']).getRaw(), 'Body one')
        self.assertEqual(storage.get('text', self.folder['d2']).getRaw(), 'BODY TWO')

    def testAbortObject(self):
        storage = AnnotationStorage()
        query   = {}
        actions = ({'fieldName'    : 'text',
                    'transform'    : makeUpper,
                     'storage'      : storage,
                    },)
        self.execute(query, actions, conditionallyAbortObject)
        self.assertEqual(storage.get('text', self.folder['d1']).getRaw(), 'Body one')
        self.assertEqual(storage.get('text', self.folder['d2']).getRaw(), 'BODY TWO')


    def testCallAfterAttribute(self):
        storage = AnnotationStorage()
        lst = []
        query = {}
        actions = ({'fieldName'    : 'text',
                    'transform'    : makeUpper,
                    'storage'      : storage,
                    'callAfter'    : callAfterAttribute
                    },)
        self.execute(query, actions, lst = lst)
        lst.sort()
        self.assertEqual(lst, ['d1: text = BODY ONE', 'd2: text = BODY TWO'])

    def testUnsetAttributeWithCustomQuery(self):
        storage = AnnotationStorage()
        query   = {'getId' : 'd1'}
        actions = ({'fieldName'    : 'text',
                    'unset'        : True,
                    'storage'      : storage,
                    },)
        self.execute(query, actions)
        self.assertEqual(storage.get('text', self.folder['d2']).getRaw(), 'Body two')
        self.assertRaises(AttributeError, storage.get, 'text', self.folder['d1'])

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestFieldMigration))
    return suite
