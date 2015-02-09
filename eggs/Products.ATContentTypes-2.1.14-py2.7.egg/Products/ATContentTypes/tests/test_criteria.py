import unittest

from DateTime import DateTime

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase
from Missing import MV

from zope.interface.verify import verifyObject
from Products.Archetypes.interfaces.base import IBaseContent
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces import IExtensibleMetadata

from Products.ATContentTypes.interfaces import IATTopicCriterion

from Products.ATContentTypes.criteria.base import ATBaseCriterion
from Products.ATContentTypes.criteria.date import ATDateCriteria
from Products.ATContentTypes.criteria.list import ATListCriterion
from Products.ATContentTypes.criteria.simpleint import ATSimpleIntCriterion
from Products.ATContentTypes.criteria.simplestring import \
    ATSimpleStringCriterion
from Products.ATContentTypes.criteria.sort import ATSortCriterion
from Products.ATContentTypes.criteria.selection import ATSelectionCriterion
from Products.ATContentTypes.criteria.daterange import ATDateRangeCriterion
from Products.ATContentTypes.criteria.reference import ATReferenceCriterion
from Products.ATContentTypes.criteria.boolean import ATBooleanCriterion
from Products.ATContentTypes.criteria.portaltype import ATPortalTypeCriterion
from Products.ATContentTypes.criteria.currentauthor import \
    ATCurrentAuthorCriterion
from Products.ATContentTypes.criteria.path import ATPathCriterion
from Products.ATContentTypes.criteria.relativepath import ATRelativePathCriterion
tests = []


class CriteriaTest(atcttestcase.ATCTSiteTestCase):

    klass = None
    portal_type = None
    title = None
    meta_type = None

    def afterSetUp(self):
        atcttestcase.ATCTSiteTestCase.afterSetUp(self)
        self.dummy = self.createDummy(self.klass)

    def createDummy(self, klass, id='dummy'):
        folder = self.folder
        if klass is not None:
            dummy = klass(id, 'dummyfield')
            # put dummy in context of portal
            folder._setObject(id, dummy)
            dummy = getattr(folder, id)
            dummy.initializeArchetype()
        else:
            dummy = None
        return dummy

    def test_000testsetup(self):
        if self.klass is not None:
            self.assertTrue(self.klass)
            self.assertTrue(self.portal_type)
            self.assertTrue(self.title)
            self.assertTrue(self.meta_type)

    def test_multipleCreateVariants(self):
        klass = self.klass
        id = 'dummy'
        field = 'dummyfield'
        if klass is not None:
            dummy = klass(id, field)
            self.assertTrue(dummy.getId(), id)
            self.assertTrue(dummy.Field(), field)

            dummy = klass(id=id, field=field)
            self.assertTrue(dummy.getId(), id)
            self.assertTrue(dummy.Field(), field)

            dummy = klass(field, oid=id)
            self.assertTrue(dummy.getId(), id)
            self.assertTrue(dummy.Field(), field)

            dummy = klass(field=field, oid=id)
            self.assertTrue(dummy.getId(), id)
            self.assertTrue(dummy.Field(), field)

    def test_typeInfo(self):
        if self.dummy is not None:
            ti = self.dummy.getTypeInfo()
            self.assertEqual(ti.getId(), self.portal_type)
            self.assertEqual(ti.Title(), self.title)
            self.assertEqual(ti.Metatype(), self.meta_type)

    def test_implements(self):
        if self.dummy is not None:
            self.assertFalse(IReferenceable.providedBy(self.dummy))
            self.assertFalse(IExtensibleMetadata.providedBy(self.dummy))
            self.assertFalse(self.dummy.isReferenceable)
            self.assertTrue(IBaseContent.providedBy(self.dummy))
            self.assertTrue(IATTopicCriterion.providedBy(self.dummy))
            self.assertTrue(verifyObject(IBaseContent, self.dummy))
            self.assertTrue(verifyObject(IATTopicCriterion, self.dummy))


class TestATBaseCriterion(CriteriaTest):
    klass = ATBaseCriterion
    title = 'Base Criterion'
    meta_type = 'ATBaseCriterion'
    portal_type = 'ATBaseCriterion'

    def test_typeInfo(self):
        # not registered
        pass

tests.append(TestATBaseCriterion)


class TestATDateCriteria(CriteriaTest):
    klass = ATDateCriteria
    title = 'Friendly Date Criteria'
    meta_type = 'ATFriendlyDateCriteria'
    portal_type = 'ATDateCriteria'

    def test_LessThanPast(self):
        # A query of the form 'Less than 14 days ago' should generate a min:max
        # query with a start 14 days in the past and an end in the present
        self.dummy.Schema()['field'].set(self.dummy, 'created')
        self.dummy.setOperation('less')
        self.dummy.setDateRange('-')
        self.dummy.setValue('14')
        expected_begin = (DateTime() - 14).earliestTime()
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'created')
        #range should start in past at the beginning of the day
        self.assertEqual(query['query'][0], expected_begin)
        # range should end today
        self.assertEqual(query['query'][1].earliestTime(),
                                                    DateTime().earliestTime())
        self.assertEqual(query['range'], 'min:max')

    def test_LessThanFuture(self):
        # A query of the form 'Less than 14 days in the future' should generate
        # a min:max query with an end 14 days in the future and a start in the
        # present
        self.dummy.Schema()['field'].set(self.dummy, 'created')
        self.dummy.setOperation('less')
        self.dummy.setDateRange('+')
        self.dummy.setValue('14')
        expected_end = (DateTime() + 14).latestTime()
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        #Range should end on future date at the end of the day
        self.assertEqual(query['query'][1], expected_end)
        #Range should start today
        self.assertEqual(query['query'][0].earliestTime(),
                                                    DateTime().earliestTime())
        self.assertEqual(query['range'], 'min:max')

    def test_MoreThanPast(self):
        # A query of the form 'More than 14 days ago' should generate a max
        # query with the value set to a date 14 days in the past.
        self.dummy.Schema()['field'].set(self.dummy, 'created')
        self.dummy.setOperation('more')
        self.dummy.setDateRange('-')
        self.dummy.setValue('14')
        expected_begin = (DateTime() - 14).earliestTime()
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        self.assertEqual(query['query'], expected_begin)
        self.assertEqual(query['range'], 'max')

    def test_MoreThanFuture(self):
        # A query of the form 'More than 14 days from now' should generate
        # a min query with the value set to a date 14 days in the future.
        self.dummy.Schema()['field'].set(self.dummy, 'created')
        self.dummy.setOperation('more')
        self.dummy.setDateRange('+')
        self.dummy.setValue('14')
        expected_begin = (DateTime() + 14).earliestTime()
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        self.assertEqual(query['query'], expected_begin)
        self.assertEqual(query['range'], 'min')

    def test_MoreThanNow(self):
        # A query of the form 'More than Now' should generate
        # a min query with the value set to the present, regardless of the
        # past future setting.
        self.dummy.Schema()['field'].set(self.dummy, 'created')
        self.dummy.setOperation('more')
        self.dummy.setDateRange('+')
        self.dummy.setValue('0')
        expected_begin = DateTime().earliestTime()
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        self.assertEqual(query['query'].earliestTime(), expected_begin)
        self.assertEqual(query['range'], 'min')
        # Change past/future setting
        self.dummy.setDateRange('-')
        self.assertEqual(query['query'].earliestTime(), expected_begin)
        self.assertEqual(query['range'], 'min')

    def test_LessThanNow(self):
        # A query of the form 'Less than Now' should generate
        # a max query with the value set to the present, regardless of the
        # past future setting.
        self.dummy.Schema()['field'].set(self.dummy, 'created')
        self.dummy.setOperation('less')
        self.dummy.setDateRange('+')
        self.dummy.setValue('0')
        expected_begin = DateTime().earliestTime()
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        self.assertEqual(query['query'].earliestTime(), expected_begin)
        self.assertEqual(query['range'], 'max')
        # Change past/future setting
        self.dummy.setDateRange('-')
        self.assertEqual(query['query'].earliestTime(), expected_begin)
        self.assertEqual(query['range'], 'max')

tests.append(TestATDateCriteria)


class TestATListCriterion(CriteriaTest):
    klass = ATListCriterion
    title = 'List Criterion'
    meta_type = 'ATListCriterion'
    portal_type = 'ATListCriterion'

    def test_list_query(self):
        self.dummy.Schema()['field'].set(self.dummy, 'Subject')
        self.dummy.setOperator('or')
        self.dummy.setValue(('1', '2', '3'))
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'Subject')
        self.assertEqual(query['query'], ('1', '2', '3'))
        self.assertEqual(query['operator'], 'or')

tests.append(TestATListCriterion)


class TestATSimpleIntCriterion(CriteriaTest):
    klass = ATSimpleIntCriterion
    title = 'Simple Int Criterion'
    meta_type = 'ATSimpleIntCriterion'
    portal_type = 'ATSimpleIntCriterion'

    def test_base_int_query(self):
        self.dummy.Schema()['field'].set(self.dummy, 'getObjPositionInParent')
        self.dummy.setDirection('')
        self.dummy.setValue(12)
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'getObjPositionInParent')
        self.assertEqual(query['query'], 12)

    def test_int_min(self):
        self.dummy.Schema()['field'].set(self.dummy, 'getObjPositionInParent')
        self.dummy.setDirection('min')
        self.dummy.setValue(12)
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        self.assertEqual(query['query'], 12)
        self.assertEqual(query['range'], 'min')

    def test_int_max(self):
        self.dummy.Schema()['field'].set(self.dummy, 'getObjPositionInParent')
        self.dummy.setDirection('max')
        self.dummy.setValue(12)
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        self.assertEqual(query['query'], 12)
        self.assertEqual(query['range'], 'max')

    def test_int_between(self):
        self.dummy.Schema()['field'].set(self.dummy, 'getObjPositionInParent')
        self.dummy.setDirection('min:max')
        self.dummy.setValue(12)
        self.dummy.setValue2(17)
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        self.assertEqual(query['query'], (12, 17))
        self.assertEqual(query['range'], 'min:max')

tests.append(TestATSimpleIntCriterion)


class TestATSimpleStringCriterion(CriteriaTest):
    klass = ATSimpleStringCriterion
    title = 'Simple String Criterion'
    meta_type = 'ATSimpleStringCriterion'
    portal_type = 'ATSimpleStringCriterion'

    def test_string_query(self):
        self.dummy.Schema()['field'].set(self.dummy, 'Subject')
        self.dummy.setValue('a*')
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'Subject')
        self.assertEqual(query, 'a*')

tests.append(TestATSimpleStringCriterion)


class TestATSortCriterion(CriteriaTest):
    klass = ATSortCriterion
    title = 'Sort Criterion'
    meta_type = 'ATSortCriterion'
    portal_type = 'ATSortCriterion'

    def test_sort_query(self):
        self.dummy.Schema()['field'].set(self.dummy, 'getObjPositionInParent')
        self.dummy.setReversed(False)
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][0], 'sort_on')
        self.assertEqual(items[0][1], 'getObjPositionInParent')

    def test_list_query_reversed(self):
        self.dummy.Schema()['field'].set(self.dummy, 'getObjPositionInParent')
        self.dummy.setReversed(True)
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0][0], 'sort_on')
        self.assertEqual(items[0][1], 'getObjPositionInParent')
        self.assertEqual(items[1][0], 'sort_order')
        self.assertEqual(items[1][1], 'reverse')

tests.append(TestATSortCriterion)


class TestATSelectionCriterion(CriteriaTest):
    klass = ATSelectionCriterion
    title = 'Selection Criterion'
    meta_type = 'ATSelectionCriterion'
    portal_type = 'ATSelectionCriterion'

    #Same as list criterion but without operator and with special vocabulary
    def test_selection_query(self):
        self.dummy.Schema()['field'].set(self.dummy, 'Subject')
        self.dummy.setValue(('1', '2', '3'))
        self.dummy.setOperator('and')
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'Subject')
        self.assertEqual(query['query'], ('1', '2', '3'))
        self.assertEqual(query['operator'], 'and')

    def test_vocabulary(self):
        #Should return some ids
        self.dummy.Schema()['field'].set(self.dummy, 'getId')
        self.assertTrue(self.dummy.getCurrentValues())

    def test_vocabulary_sorted(self):
        #Should return sorted ids
        self.dummy.Schema()['field'].set(self.dummy, 'getId')
        orig_vocab = [a.lower() for a in list(self.dummy.getCurrentValues())]
        sorted_vocab = orig_vocab[:]
        sorted_vocab.sort()
        self.assertEqual(orig_vocab, sorted_vocab)

tests.append(TestATSelectionCriterion)


class TestATDateRangeCriterion(CriteriaTest):
    klass = ATDateRangeCriterion
    title = 'Date Range Criterion'
    meta_type = 'ATDateRangeCriterion'
    portal_type = 'ATDateRangeCriterion'

    def test_date_range_query(self):
        self.dummy.Schema()['field'].set(self.dummy, 'created')
        now = DateTime()
        self.dummy.setStart(now)
        self.dummy.setEnd(now + 5)
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'created')
        self.assertEqual(query['query'][0], now)
        self.assertEqual(query['query'][1], now + 5)
        self.assertEqual(query['range'], 'min:max')

tests.append(TestATDateRangeCriterion)


class TestATReferenceCriterion(CriteriaTest):
    klass = ATReferenceCriterion
    title = 'Reference Criterion'
    meta_type = 'ATReferenceCriterion'
    portal_type = 'ATReferenceCriterion'

    #Same as list criterion but without operator and with special vocabulary
    def test_reference_query(self):
        self.dummy.Schema()['field'].set(self.dummy, 'getRawRelatedItems')
        self.folder.invokeFactory('Document', 'doc1')
        uid = self.folder.doc1.UID()
        self.dummy.setValue((uid,))
        self.dummy.setOperator('and')
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'getRawRelatedItems')
        self.assertEqual(query['query'], (uid,))
        self.assertEqual(query['operator'], 'and')

    def test_reference_vocab(self):
        self.dummy.Schema()['field'].set(self.dummy, 'getRawRelatedItems')
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.invokeFactory('Document', 'doc2')
        uid1 = self.folder.doc1.UID()
        uid2 = self.folder.doc2.UID()
        self.folder.doc1.setRelatedItems([uid2])
        self.folder.doc2.setRelatedItems([uid1])
        self.folder.doc1.reindexObject()
        self.folder.doc2.reindexObject()
        vocab = self.dummy.getCurrentValues()
        self.assertEqual(len(vocab), 2)
        self.assertTrue(uid1 in vocab.keys())
        self.assertTrue(uid2 in vocab.keys())
        self.assertTrue('doc1' in vocab.values())
        self.assertTrue('doc2' in vocab.values())

tests.append(TestATReferenceCriterion)


class TestATBooleanCriterion(CriteriaTest):
    klass = ATBooleanCriterion
    title = 'Boolean Criterion'
    meta_type = 'ATBooleanCriterion'
    portal_type = 'ATBooleanCriterion'

    def test_boolean_query_true(self):
        self.dummy.Schema()['field'].set(self.dummy, 'isPrincipiaFolderish')
        self.dummy.setBool(True)
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'isPrincipiaFolderish')
        self.assertEqual(query, [1, True, '1', 'True'])

    def test_boolean_query_false(self):
        self.dummy.Schema()['field'].set(self.dummy, 'isPrincipiaFolderish')
        self.dummy.setBool(False)
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'isPrincipiaFolderish')
        self.assertEqual(query,
                         [0, '', False, '0', 'False', None, (), [], {}, MV])

tests.append(TestATBooleanCriterion)


class TestATPortalTypeCriterion(CriteriaTest):
    klass = ATPortalTypeCriterion
    title = 'Portal Types Criterion'
    meta_type = 'ATPortalTypeCriterion'
    portal_type = 'ATPortalTypeCriterion'

    #Same as list criterion but without operator and with special vocabulary
    def test_portaltype_query(self):
        self.dummy.Schema()['field'].set(self.dummy, 'portal_type')
        self.dummy.setValue(('Document', 'Folder', 'Topic'))
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'portal_type')
        self.assertEqual(query, ('Document', 'Folder', 'Topic'))

    def test_vocabulary(self):
        #Should return standard types, but not blacklisted types
        self.dummy.Schema()['field'].set(self.dummy, 'portal_types')
        self.assertTrue('Document' in self.dummy.getCurrentValues().keys())
        self.assertTrue('ATSimpleStringCriterion' not in self.dummy.getCurrentValues().keys())

    def test_vocabulary_sorts_by_title(self):
        #Should return standard types, but not blacklisted types
        self.dummy.Schema()['field'].set(self.dummy, 'Type')
        type_names = self.dummy.getCurrentValues().values()
        self.assertTrue(type_names.index('Page') > type_names.index('Event'))
        self.dummy.Schema()['field'].set(self.dummy, 'portal_types')
        type_names = self.dummy.getCurrentValues().values()
        self.assertTrue(type_names.index('Page') > type_names.index('Event'))

    def test_type_ids_names(self):
        self.dummy.Schema()['field'].set(self.dummy, 'Type')
        type_ids = self.dummy.getCurrentValues().keys()
        type_names = self.dummy.getCurrentValues().values()
        self.assertTrue('Page' in type_ids)
        self.assertTrue('Page' in type_names)
        self.assertFalse('Document' in type_ids)
        self.assertFalse('Document' in type_names)
        # use type title everytime
        self.dummy.Schema()['field'].set(self.dummy, 'portal_type')
        type_ids = self.dummy.getCurrentValues().keys()
        type_names = self.dummy.getCurrentValues().values()
        self.assertTrue('Document' in type_ids)
        self.assertTrue('Page' in type_names)
        self.assertFalse('Page' in type_ids)
        self.assertFalse('Document' in type_names)
        # ensure that blacklisted types aren't included
        self.assertFalse('Simple String Criterion' in type_ids)


tests.append(TestATPortalTypeCriterion)


class TestATCurrentAuthorCriterion(CriteriaTest):
    klass = ATCurrentAuthorCriterion
    title = 'Current Author Criterion'
    meta_type = 'ATCurrentAuthorCriterion'
    portal_type = 'ATCurrentAuthorCriterion'

    def afterSetUp(self):
        CriteriaTest.afterSetUp(self)
        self.portal.acl_users._doAddUser('member', 'secret', ['Member'], [])
        self.portal.acl_users._doAddUser('reviewer', 'secret', ['Reviewer'], [])

    def test_author_query(self):
        self.dummy.Schema()['field'].set(self.dummy, 'creator')
        self.login('member')
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'creator')
        self.assertEqual(query, 'member')
        self.login('reviewer')
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'creator')
        self.assertEqual(query, 'reviewer')

tests.append(TestATCurrentAuthorCriterion)


class TestATRelativePathCriterion(CriteriaTest):
    klass = ATRelativePathCriterion
    title = 'Relative Path Criterion'
    meta_type = 'ATRelativePathCriterion'
    portal_type = 'ATRelativePathCriterion'

    def afterSetUp(self):
        CriteriaTest.afterSetUp(self)
        self.setRoles(['Manager'])
        # build folder structure
        self.portal.invokeFactory('Folder', 'folderA')
        self.portal.invokeFactory('Folder', 'folderB')
        self.portal.folderA.invokeFactory('Folder', 'folderA1')
        self.portal.folderB.invokeFactory('Folder', 'folderB1')

        # create topic in folderA1
        self.portal.folderA.folderA1.invokeFactory('Topic', 'new_topic', title='New Topic')

        self.topic = self.portal.folderA.folderA1.new_topic
        # Add a path criterion
        self.path_crit = self.topic.addCriterion('path', 'ATRelativePathCriterion')

    def test_relative_path_query1(self):
        self.path_crit.setRelativePath('..')  # should give the parent==folderA1
        self.assertTrue(self.path_crit.getCriteriaItems() == (('path', {'query': '/plone/folderA/folderA1', 'depth': 1}),))

    def test_relative_path_query2(self):
        self.path_crit.setRelativePath('../..')  # should give folderA
        self.assertTrue(self.path_crit.getCriteriaItems() == (('path', {'query': '/plone/folderA', 'depth': 1}),))

    def test_relative_path_query3(self):
        self.path_crit.setRelativePath('../../..')  # should give the /plone (portal)
        self.assertTrue(self.path_crit.getCriteriaItems() == (('path', {'query': '/plone', 'depth': 1}),))

    def test_relative_path_query4(self):
        self.path_crit.setRelativePath('../../../../../../..')  # should give the /plone (portal): cannot go higher than the portal
        self.assertTrue(self.path_crit.getCriteriaItems() == (('path', {'query': '/plone', 'depth': 1}),))

    def test_relative_path_query5(self):
        self.path_crit.setRelativePath('../../../folderB')  # should give folderB
        self.assertTrue(self.path_crit.getCriteriaItems() == (('path', {'query': '/plone/folderB', 'depth': 1}),))

    def test_relative_path_query6(self):
        self.path_crit.setRelativePath('/folderB')  # should give folderB also (absolute paths are supported)
        self.assertTrue(self.path_crit.getCriteriaItems() == (('path', {'query': '/plone/folderB', 'depth': 1}),))

    def test_relative_path_query7(self):
        self.path_crit.setRelativePath('../../folderA1/../../folderB/folderB1/..')   # should give folderB
        self.assertTrue(self.path_crit.getCriteriaItems() == (('path', {'query': '/plone/folderB', 'depth': 1}),))

    def test_relative_path_query8(self):
        self.path_crit.setRelativePath('.')  # should give the new_topic
        self.assertTrue(self.path_crit.getCriteriaItems() == (('path', {'query': '/plone/folderA/folderA1/new_topic', 'depth': 1}),))

    def test_relative_path_query9(self):
        # Acquisition can mess us up, for example when a BrowserView
        # is in the acquisition chain, like in
        # plone.app.content.browser.foldercontents
        self.path_crit.setRelativePath('..')  # should give the parent==folderA1
        from Products.Five import BrowserView
        view = BrowserView(self.topic, self.topic.REQUEST)
        criterion = view.context.getCriterion('path_ATRelativePathCriterion')
        self.assertTrue(criterion.getCriteriaItems() == (('path', {'query': '/plone/folderA/folderA1', 'depth': 1}),))


tests.append(TestATRelativePathCriterion)


class TestATPathCriterion(CriteriaTest):
    klass = ATPathCriterion
    title = 'Path Criterion'
    meta_type = 'ATPathCriterion'
    portal_type = 'ATPathCriterion'

    def test_path_query(self):
        # ensure that the path and recurse settings result in a proper query
        self.dummy.Schema()['field'].set(self.dummy, 'path')
        self.folder.invokeFactory('Document', 'doc1')
        uid = self.folder.doc1.UID()
        self.dummy.setValue((uid,))
        self.dummy.setRecurse(True)
        items = self.dummy.getCriteriaItems()
        self.assertEqual(len(items), 1)
        query = items[0][1]
        field = items[0][0]
        self.assertEqual(field, 'path')
        self.assertEqual(tuple(query['query']), ('/plone/Members/test_user_1_/doc1',))
        self.assertEqual(query['depth'], -1)
        self.dummy.setRecurse(False)
        items = self.dummy.getCriteriaItems()
        query = items[0][1]
        self.assertEqual(query['depth'], 1)

    # Some reference errors were making this impossible
    def test_path_criteria_can_be_removed(self):
        self.setRoles(['Manager', 'Member'])
        self.folder.invokeFactory('Topic', 'new_topic', title='New Topic')
        topic = self.folder.new_topic
        # Add a path criterion
        path_crit = topic.addCriterion('path', 'ATPathCriterion')
        # Give it a reference
        path_crit.setValue([topic.UID()])
        # The error is masked when not in debug mode or as manager, though it
        # still has consequences
        from App.config import getConfiguration
        config = getConfiguration()
        orig_debug = config.debug_mode
        config.debug_mode = True
        self.setRoles(['Member'])
        # Delete the topic
        try:
            self.folder.manage_delObjects(['new_topic'])
        except AttributeError:
            config.debug_mode = orig_debug
            self.fail("Deleting a topic with path criteria raises an error!")
        config.debug_mode = orig_debug

tests.append(TestATPathCriterion)


class TestCriterionRegistry(atcttestcase.ATCTSiteTestCase):

    def afterSetUp(self):
        from Products.ATContentTypes.criteria import _criterionRegistry
        atcttestcase.ATCTSiteTestCase.afterSetUp(self)
        self.crit_registry = _criterionRegistry

    def testRegisterCriteria(self):
        # Ensure that the criteria registering and unregistering mechanism
        # works as expected
        # check if the expected criteria is there
        self.assertTrue(ATDateCriteria in self.crit_registry.listCriteria())
        self.assertTrue(self.crit_registry.indicesByCriterion('ATFriendlyDateCriteria'))
        # remove and ensure that it was removed
        self.crit_registry.unregister(ATDateCriteria)
        self.assertFalse(ATDateCriteria in self.crit_registry.listCriteria())
        # add and ensure that it was added
        self.crit_registry.register(ATDateCriteria, ('Bogus Index',))
        self.assertTrue(ATDateCriteria in self.crit_registry.listCriteria())
        self.assertEqual(self.crit_registry.indicesByCriterion('ATFriendlyDateCriteria'),
                                                        ('Bogus Index',))

    def testCriteriaIndexLookupOnBadIndex(self):
        # Make sure we don't throw errors when someone has a non-default index
        # type in their catalog.
        self.crit_registry.criteriaByIndex('My Bad Index Type')

tests.append(TestCriterionRegistry)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
