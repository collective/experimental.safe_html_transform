from z3c.relationfield import RelationValue
from zope.component import getUtility
from zope.interface import Interface
from zope.intid.interfaces import IIntIds
from plone.app.layout.viewlets.tests.base import ViewletsTestCase
from plone.app.layout.viewlets.content import DocumentBylineViewlet
from plone.app.layout.viewlets.content import ContentRelatedItems
from plone.locking.tests import addMember
from plone.locking.interfaces import ILockable
from plone.memoize.instance import Memojito

from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.ExtensibleMetadata import _zone

try:
    import pkg_resources
    pkg_resources.get_distribution('plone.app.relationfield')
except pkg_resources.DistributionNotFound:
    HAS_DEXTERITY = False
    pass
else:
    HAS_DEXTERITY = True
    from plone.dexterity.fti import DexterityFTI
    class IMyDexterityItem(Interface):
        """ Dexterity test type
        """


class TestDocumentBylineViewletView(ViewletsTestCase):
    """
    Test the document by line viewlet
    """
    def afterSetUp(self):
        addMember(self, 'Alan', roles=('Member', 'Manager'))
        addMember(self, 'Ano', roles=())

    def test_anonymous_locked_icon(self):
        request = self.app.REQUEST
        self.setRoles(['Manager', 'Member'])
        self.portal.invokeFactory('Document', 'd1')
        context = getattr(self.portal, 'd1')
        viewlet = DocumentBylineViewlet(context, request, None, None)
        viewlet.update()
        ILockable(context).lock()
        self.login('Ano')
        viewlet = DocumentBylineViewlet(context, request, None, None)
        viewlet.update()
        self.assertEqual(viewlet.locked_icon(), "")

    def test_locked_icon(self):
        request = self.app.REQUEST
        self.setRoles(['Manager', 'Member'])
        self.portal.invokeFactory('Document', 'd1')
        context = getattr(self.portal, 'd1')
        viewlet = DocumentBylineViewlet(context, request, None, None)
        viewlet.update()
        self.assertEqual(viewlet.locked_icon(), "")
        ILockable(context).lock()
        lockIconUrl = '<img src="http://nohost/plone/lock_icon.png" alt="" \
title="Locked" height="16" width="16" />'
        self.assertEqual(viewlet.locked_icon(), lockIconUrl)
    
    def test_pub_date(self):
        request = self.app.REQUEST
        self.login('Alan')
        self.portal.invokeFactory('Document', 'd1')
        context = getattr(self.portal, 'd1')
        
        # configure our portal to enable publication date on pages globally on
        # the site
        properties = getToolByName(context, 'portal_properties')
        site_properties = getattr(properties, 'site_properties')
        site_properties.displayPublicationDateInByline = True

        self.login('Ano')
        viewlet = DocumentBylineViewlet(context, request, None, None)
        viewlet.update()
        
        # publication date should be None as there is not Effective date set for
        # our document yet
        self.assertEqual(viewlet.pub_date(), None)

        # now set effective date for our document
        effective = DateTime()
        context.setEffectiveDate(effective)
        self.assertEqual(viewlet.pub_date(), DateTime(effective.ISO8601()))
        
        # now switch off publication date globally on the site and see if
        # viewlet returns None for publication date
        site_properties.displayPublicationDateInByline = False
        self.assertEqual(viewlet.pub_date(), None)

class TestRelatedItemsViewlet(ViewletsTestCase):

    def afterSetUp(self):
        self.folder.invokeFactory('Document', 'doc1', title='Document 1')
        self.folder.invokeFactory('Document', 'doc2', title='Document 2')
        self.folder.invokeFactory('Document', 'doc3', title='Document 3')
        self.folder.doc1.setRelatedItems([self.folder.doc2, self.folder.doc3])

    def testRelatedItems(self):
        request = self.app.REQUEST
        viewlet = ContentRelatedItems(self.folder.doc1, request, None, None)
        viewlet.update()
        related = viewlet.related_items()
        self.assertEqual([x.Title for x in related], ['Document 2', 'Document 3'])


class TestDexterityRelatedItemsViewlet(ViewletsTestCase):

    def afterSetUp(self):
        """ create some sample content to test with """
        if not HAS_DEXTERITY:
            return
        self.setRoles(('Manager',))
        fti = DexterityFTI('Dexterity Item with relatedItems behavior')
        self.portal.portal_types._setObject('Dexterity Item with relatedItems behavior', fti)
        fti.klass = 'plone.dexterity.content.Item'
        fti.schema = 'plone.app.layout.viewlets.tests.test_content.IMyDexterityItem'
        fti.behaviors = ('plone.app.relationfield.behavior.IRelatedItems',)
        fti = DexterityFTI('Dexterity Item without relatedItems behavior')
        self.portal.portal_types._setObject('Dexterity Item without relatedItems behavior', fti)
        fti.klass = 'plone.dexterity.content.Item'
        fti.schema = 'plone.app.layout.viewlets.tests.test_content.IMyDexterityItem'
        self.folder.invokeFactory('Document', 'doc1', title='Document 1')
        self.folder.invokeFactory('Document', 'doc2', title='Document 2')
        self.folder.invokeFactory('Dexterity Item with relatedItems behavior', 'dex1')
        self.folder.invokeFactory('Dexterity Item with relatedItems behavior', 'dex2')
        self.folder.invokeFactory('Dexterity Item without relatedItems behavior', 'dex3')
        self.portal.portal_quickinstaller.installProduct('plone.app.intid')
        intids = getUtility(IIntIds)
        self.folder.dex1.relatedItems = [RelationValue(intids.getId(self.folder.doc1)),
                                         RelationValue(intids.getId(self.folder.doc2))]

    def testDexterityRelatedItems(self):
        request = self.app.REQUEST
        viewlet = ContentRelatedItems(self.folder.dex1, request, None, None)
        viewlet.update()
        related = viewlet.related_items()
        self.assertEqual([x.id for x in related], ['doc1', 'doc2'])

        # TODO: we should test with non-published objects and anonymous users
        #       but current workflow has no transition to make an item private

    def testDexterityEmptyRelatedItems(self):
        request = self.app.REQUEST
        viewlet = ContentRelatedItems(self.folder.dex2, request, None, None)
        viewlet.update()
        related = viewlet.related_items()
        self.assertEqual(len(related), 0)

    def testDexterityWithoutRelatedItemsBehavior(self):
        request = self.app.REQUEST
        viewlet = ContentRelatedItems(self.folder.dex2, request, None, None)
        viewlet.update()
        related = viewlet.related_items()
        self.assertEqual(len(related), 0)

    def testDexterityFolderRelatedItems(self):
        """
        Related items viewlet doesn't include related folder's descendants.
        """
        self.assertTrue(
            self.folder.contentValues(), 'Folder is missing descendants')

        intids = getUtility(IIntIds)
        self.folder.dex1.relatedItems = [
            RelationValue(intids.getId(self.folder))]

        request = self.app.REQUEST
        viewlet = ContentRelatedItems(self.folder.dex1, request, None, None)
        viewlet.update()
        related = viewlet.related_items()
        self.assertEqual(len(related), 1)


def test_suite():
    from unittest import defaultTestLoader
    return defaultTestLoader.loadTestsFromName(__name__)
