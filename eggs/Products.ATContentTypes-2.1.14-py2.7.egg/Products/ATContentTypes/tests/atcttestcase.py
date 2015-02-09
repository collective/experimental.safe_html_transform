from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase
from Products.PloneTestCase.layer import PloneSiteLayer
from Products.PloneTestCase.setup import default_user
from Products.PloneTestCase.setup import default_password
from Products.PloneTestCase.setup import portal_name
from Products.PloneTestCase.setup import portal_owner
ZopeTestCase.installProduct('SiteAccess')
PloneTestCase.setupPloneSite()

import os

from zope.interface.verify import verifyObject

from Products.CMFCore.interfaces import IDublinCore
from Products.CMFCore.interfaces import IMutableDublinCore
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.CMFDynamicViewFTI.interface import ISelectableBrowserDefault
from Products.Archetypes.atapi import AttributeStorage
from Products.Archetypes.atapi import DisplayList
from Products.Archetypes.atapi import IdWidget
from Products.Archetypes.atapi import RFC822Marshaller
from Products.Archetypes.atapi import MetadataStorage
from Products.Archetypes.atapi import TextAreaWidget
from Products.Archetypes.interfaces.base import IBaseContent
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.templatemixin import ITemplateMixin
from Products.Archetypes.tests.test_baseschema import BaseSchemaTest
from archetypes.referencebrowserwidget import ReferenceBrowserWidget

from plone.app.blob.markings import markAs

from Products.ATContentTypes.config import HAS_LINGUA_PLONE
from Products.ATContentTypes.interfaces import IATContentType
from Products.ATContentTypes.tests.utils import dcEdit
from Products.ATContentTypes.tests.utils import EmptyValidator
from Products.ATContentTypes.tests.utils import idValidator

test_home = os.path.dirname(__file__)


class ATCTSiteTestCase(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        # BBB - make sure we can regression test the deprecated types:
        #  - Large Plone Folder
        #  - Topic
        user = self.portal.acl_users.getUserById(default_user)
        orig_roles = self.portal.acl_users.portal_role_manager.getRolesForPrincipal(user)
        self.setRoles(['Manager'])
        ttool = self.portal.portal_types
        cb_copy_data = ttool.manage_copyObjects(['Folder'])
        paste_data = ttool.manage_pasteObjects(cb_copy_data)
        temp_id = paste_data[0]['new_id']
        ttool.manage_renameObject(temp_id, 'Large Plone Folder')
        lpf = ttool['Large Plone Folder']
        lpf.title = 'Large Folder'
        lpf.product = 'ATContentTypes'
        lpf.content_meta_type = 'ATBTreeFolder'
        lpf.factory = 'addATBTreeFolder'
        ttool['Topic'].global_allow = True
        self.setRoles(orig_roles)


class ATCTFunctionalSiteTestCase(PloneTestCase.FunctionalTestCase, ATCTSiteTestCase):
    pass


class ATCTTypeTestCase(ATCTSiteTestCase):
    """AT Content Types test

    Tests some basics of a type
    """

    klass = None
    portal_type = ''
    cmf_portal_type = ''
    title = ''
    meta_type = ''

    def afterSetUp(self):
        super(ATCTTypeTestCase, self).afterSetUp()
        self._ATCT = self._createType(self.folder, self.portal_type, 'ATCT')

    def _createType(self, context, portal_type, id, **kwargs):
        """Helper method to create a new type
        """
        ttool = getToolByName(context, 'portal_types')
        cat = self.portal.portal_catalog

        fti = ttool.getTypeInfo(portal_type)
        fti.constructInstance(context, id, **kwargs)
        obj = getattr(context.aq_inner.aq_explicit, id)
        cat.indexObject(obj)
        return obj

    def test_000testsetup(self):
        # test if we really have the right test setup
        # vars
        self.assertTrue(self.klass)
        self.assertTrue(self.portal_type)
        self.assertTrue(self.title)
        self.assertTrue(self.meta_type)

        # portal types
        self.assertEqual(self._ATCT.portal_type, self.portal_type)

        # classes
        atct_class = self._ATCT.__class__
        self.assertEqual(self.klass, atct_class)

    def test_dcEdit(self):
        new = self._ATCT
        dcEdit(new)

    def test_typeInfo(self):
        ti = self._ATCT.getTypeInfo()
        self.assertEqual(ti.getId(), self.portal_type)
        self.assertEqual(ti.Title(), self.title)

    def test_doesImplementDC(self):
        self.assertTrue(verifyObject(IDublinCore, self._ATCT))
        self.assertTrue(verifyObject(IMutableDublinCore, self._ATCT))

    def test_doesImplementATCT(self):
        self.assertTrue(IATContentType.providedBy(self._ATCT))
        self.assertTrue(verifyObject(IATContentType, self._ATCT))

    def test_doesImplementAT(self):
        self.assertTrue(IBaseContent.providedBy(self._ATCT))
        self.assertTrue(IReferenceable.providedBy(self._ATCT))
        self.assertTrue(verifyObject(IBaseContent, self._ATCT))
        self.assertTrue(verifyObject(IReferenceable, self._ATCT))

    def test_implementsTranslateable(self):
        # lingua plone is adding the ITranslatable interface to all types
        if not HAS_LINGUA_PLONE:
            return
        else:
            from Products.LinguaPlone.interfaces import ITranslatable
            self.assertTrue(ITranslatable.providedBy(self._ATCT))
            self.assertTrue(verifyObject(ITranslatable, self._ATCT))

    def test_not_implements_ITemplateMixin(self):
        self.assertFalse(ITemplateMixin.providedBy(self._ATCT))

    def test_implements_ISelectableBrowserDefault(self):
        iface = ISelectableBrowserDefault
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def compareDC(self, first, second=None, **kwargs):
        """
        """
        if second != None:
            title = second.Title()
            description = second.Description()
        else:
            title = kwargs.get('title')
            description = kwargs.get('description')

        self.assertEqual(first.Title(), title)
        self.assertEqual(first.Description(), description)

    def test_idValidation(self):
        self.setRoles(['Manager', 'Member'])  # for ATTopic
        asdf = self._createType(self.folder, self.portal_type, 'asdf')
        self._createType(self.folder, self.portal_type, 'asdf2')
        self.setRoles(['Member'])

        request = self.app.REQUEST

        # invalid ids
        ids = ['asdf2', '???', '/asdf2', ' asdf2', 'portal_workflow',
            'portal_url']
        for id in ids:
            request.form = {'id': id, 'fieldset': 'default'}
            self.assertNotEquals(asdf.validate(REQUEST=request), {}, "Not catched id: %s" % id)

        # valid ids
        ids = ['', 'abcd', 'blafasel']
        for id in ids:
            request.form = {'id': id}
            self.assertEqual(asdf.validate(REQUEST=request), {})

    def test_schema_marshall(self):
        atct = self._ATCT
        schema = atct.Schema()
        marshall = schema.getLayerImpl('marshall')
        marshallers = [RFC822Marshaller]
        try:
            from Products.Marshall import ControlledMarshaller
            marshallers.append(ControlledMarshaller)
        except ImportError:
            pass
        self.assertTrue(isinstance(marshall, tuple(marshallers)), marshall)

    def beforeTearDown(self):
        self.logout()


class ATCTFieldTestCase(ATCTSiteTestCase, BaseSchemaTest):
    """ ATContentTypes test including AT schema tests """

    layer = PloneSiteLayer

    def afterSetUp(self):
        # initalize the portal but not the base schema test
        # because we want to overwrite the dummy and don't need it
        ATCTSiteTestCase.afterSetUp(self)
        self.setRoles(['Manager'])

    def createDummy(self, klass, id='dummy', subtype=None):
        portal = self.portal
        dummy = klass(oid=id)
        markAs(dummy, subtype)
        # put dummy in context of portal
        dummy = dummy.__of__(portal)
        portal.dummy = dummy
        dummy.initializeArchetype()
        return dummy

    def test_description(self):
        dummy = self._dummy
        field = dummy.getField('description')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertEqual(field.required, False)
        self.assertEqual(field.default, '')
        self.assertEqual(field.searchable, True)
        self.assertEqual(field.primary, False)
        vocab = field.vocabulary
        self.assertEqual(vocab, ())
        self.assertEqual(field.enforceVocabulary, False)
        self.assertEqual(field.multiValued, False)
        self.assertEqual(field.isMetadata, True)
        self.assertEqual(field.accessor, 'Description')
        self.assertEqual(field.mutator, 'setDescription')
        self.assertEqual(field.edit_accessor, 'getRawDescription')
        self.assertEqual(field.read_permission, View)
        self.assertEqual(field.write_permission, ModifyPortalContent)
        self.assertEqual(field.generateMode, 'mVc')
        #self.assertTrue(field.generateMode == 'veVc', field.generateMode)
        self.assertEqual(field.force, '')
        self.assertEqual(field.type, 'text')
        self.assertTrue(isinstance(field.storage, MetadataStorage))
        self.assertTrue(field.getLayerImpl('storage') == MetadataStorage())
        self.assertEqual(field.validators, EmptyValidator)
        self.assertTrue(isinstance(field.widget, TextAreaWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, DisplayList))
        self.assertEqual(tuple(vocab), ())

    def test_id(self):
        dummy = self._dummy
        field = dummy.getField('id')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertEqual(field.required, False)
        self.assertEqual(field.default, None)
        self.assertEqual(field.searchable, True)
        self.assertEqual(getattr(field, 'primary', None), None)
        vocab = field.vocabulary
        self.assertEqual(vocab, ())
        self.assertEqual(field.enforceVocabulary, False)
        self.assertEqual(field.multiValued, False)
        self.assertEqual(field.isMetadata, False)
        self.assertEqual(field.accessor, 'getId')
        self.assertEqual(field.mutator, 'setId')
        self.assertEqual(field.edit_accessor, 'getRawId')
        self.assertEqual(field.read_permission, View)
        self.assertEqual(field.write_permission, ModifyPortalContent)
        self.assertEqual(field.generateMode, 'veVc')
        self.assertEqual(field.force, '')
        self.assertEqual(field.type, 'string')
        self.assertTrue(isinstance(field.storage, AttributeStorage))
        self.assertTrue(field.getLayerImpl('storage') == AttributeStorage())
        self.assertEqual(field.validators, idValidator)
        self.assertTrue(isinstance(field.widget, IdWidget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, DisplayList))
        self.assertEqual(tuple(vocab), ())

    def test_relateditems(self):
        dummy = self._dummy
        field = dummy.getField('relatedItems')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertEqual(field.required, False)
        self.assertEqual(field.default, None)
        self.assertEqual(field.searchable, False)
        self.assertEqual(getattr(field, 'primary', None), None)
        vocab = field.vocabulary
        self.assertEqual(vocab, ())
        self.assertEqual(field.enforceVocabulary, False)
        self.assertEqual(field.multiValued, True)
        self.assertEqual(field.isMetadata, True)
        self.assertEqual(field.accessor, 'getRelatedItems')
        self.assertEqual(field.mutator, 'setRelatedItems')
        self.assertEqual(field.edit_accessor, 'getRawRelatedItems')
        self.assertEqual(field.read_permission, View)
        self.assertEqual(field.write_permission, ModifyPortalContent)
        self.assertEqual(field.generateMode, 'veVc')
        self.assertEqual(field.force, '')
        self.assertEqual(field.type, 'reference')
        self.assertTrue(isinstance(field.storage, AttributeStorage))
        self.assertTrue(field.getLayerImpl('storage') == AttributeStorage())
        self.assertEqual(field.validators, EmptyValidator)
        self.assertTrue(isinstance(field.widget, ReferenceBrowserWidget))
        self.assertTrue(field.widget.allow_sorting, u'field and widget need to enable sorting')
        self.assertTrue(field.referencesSortable, u'field and widget need to enable sorting')

        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, DisplayList))
