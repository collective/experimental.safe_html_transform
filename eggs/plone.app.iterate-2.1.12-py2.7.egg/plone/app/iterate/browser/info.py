"""
$Id: base.py 1808 2007-02-06 11:39:11Z hazmat $
"""

from zope.interface import implements

from zope.viewlet.interfaces import IViewlet

from DateTime import DateTime
from AccessControl import getSecurityManager

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName

from plone.app.iterate.permissions import CheckoutPermission
from plone.app.iterate.util import get_storage
from plone.app.iterate.interfaces import keys, IBaseline

from plone.app.iterate.relation import WorkingCopyRelation

from plone.memoize.instance import memoize
from Products.CMFPlone.log import logger

class BaseInfoViewlet( BrowserView ):

    implements( IViewlet )

    def __init__( self, context, request, view, manager ):
        super( BaseInfoViewlet, self ).__init__( context, request )
        self.__parent__ = view
        self.view = view
        self.manager = manager

    def update( self ):
        pass

    def render( self ):
        raise NotImplementedError

    @memoize
    def created( self ):
        time = self.properties.get( keys.checkout_time, DateTime() )
        util = getToolByName(self.context, 'translation_service')
        return util.ulocalized_time(time, context=self.context, domain='plonelocales')

    @memoize
    def creator( self ):
        user_id = self.properties.get( keys.checkout_user )
        membership = getToolByName(self.context, 'portal_membership')
        if not user_id:
            return membership.getAuthenticatedMember()
        return membership.getMemberById( user_id )

    @memoize
    def creator_url( self ):
        creator = self.creator()
        if creator is not None:
            portal_url = getToolByName(self.context, 'portal_url')
            return "%s/author/%s" % ( portal_url(), creator.getId() )


    @memoize
    def creator_name( self ):
        creator = self.creator()
        if creator is not None:
            return creator.getProperty('fullname') or creator.getId()
        # User is not known by PAS. This may be due to LDAP issues, so we keep
        # the user and log this.
        name = self.properties.get(keys.checkout_user)
        if IBaseline.providedBy(self.context):
            warning_tpl = "%s is a baseline of a plone.app.iterate checkout by an unknown user id '%s'"
        else:
            # IWorkingCopy.providedBy(self.context)
            warning_tpl = "%s is a working copy of a plone.app.iterate checkout by an unknown user id '%s'"
        logger.warning(warning_tpl, self.context, name)
        return name

    @property
    @memoize
    def properties( self ):
        wc_ref = self._getReference()
        if wc_ref is not None:
            return get_storage( wc_ref )
        else:
            return {}

    def _getReference( self ):
        raise NotImplemented

class BaselineInfoViewlet( BaseInfoViewlet ):

    index = ViewPageTemplateFile('info_baseline.pt')

    def render(self):
        sm = getSecurityManager()
        working_copy = self.working_copy()
        if working_copy is not None and (
                sm.checkPermission(ModifyPortalContent, self.context) or
                sm.checkPermission(CheckoutPermission, self.context) or
                sm.checkPermission(ModifyPortalContent, working_copy)):
            return self.index()
        else:
            return ""

    @memoize
    def working_copy( self ):
        refs = self.context.getBRefs( WorkingCopyRelation.relationship )
        if len( refs ) > 0:
            return refs[0]
        else:
            return None

    def _getReference( self ):
        refs = self.context.getBackReferenceImpl( WorkingCopyRelation.relationship )
        if len( refs ) > 0:
            return refs[0]
        else:
            return None

class CheckoutInfoViewlet( BaseInfoViewlet ):

    index = ViewPageTemplateFile('info_checkout.pt')

    def render(self):
        sm = getSecurityManager()
        baseline = self.baseline()
        if baseline is not None and (
                sm.checkPermission(ModifyPortalContent, self.context) or
                sm.checkPermission(CheckoutPermission, baseline)):
            return self.index()
        else:
            return ""

    @memoize
    def baseline( self ):
        refs = self.context.getReferences( WorkingCopyRelation.relationship )
        if len( refs ) > 0:
            return refs[0]
        else:
            return None

    def _getReference( self ):
        refs = self.context.getReferenceImpl( WorkingCopyRelation.relationship )
        if len( refs ) > 0:
            return refs[0]
        else:
            return None

