"""Mixin class for selectable views

This module contains a mixin-class to support selecting default layout
templates and/or default pages (in the style of default_page/index_html).
The implementation extends TemplateMixin from Archetypes, and implements
the ISelectableBrowserDefault interface from CMFPlone.
"""

from zope.interface import implements
import zope.component
from zope.browsermenu.interfaces import IBrowserMenu

from ExtensionClass import Base
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Acquisition import aq_base
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import View

from Products.CMFDynamicViewFTI.permissions import ModifyViewTemplate
from Products.CMFDynamicViewFTI.fti import DynamicViewTypeInformation

from Products.CMFDynamicViewFTI.interfaces import ISelectableBrowserDefault

_marker = object()
fti_meta_type = DynamicViewTypeInformation.meta_type

class BrowserDefaultMixin(Base):
    """Mixin class for content types using the dynamic view FTI

    Allow the user to select a layout template (in the same way as
    TemplateMixin in Archetypes does), and/or to set a contained
    object's id as a default_page (acting in the same way as index_html)

    Note: folderish content types should overwrite HEAD like ATContentTypes
    """
    implements(ISelectableBrowserDefault)

    _at_fti_meta_type = fti_meta_type
    aliases = {
        '(Default)'  : '(dynamic view)',
        'view'       : '(selected layout)',
        'edit'       : 'base_edit',
        'properties' : 'base_metadata',
        'sharing'    : 'folder_localrole_form',
        'gethtml'    : '',
        'mkdir'      : '',
        }

    default_view = "base_view"
    suppl_views = ()

    security = ClassSecurityInfo()

    security.declareProtected(View, 'defaultView')
    def defaultView(self, request=None):
        """
        Get the actual view to use. If a default page is set, its id will
        be returned. Else, the current layout's page template id is returned.
        """
        fti = self.getTypeInfo()
        if fti is None:
            return self.default_view
        else:
            return fti.defaultView(self)

    security.declareProtected(View, '__call__')
    def __call__(self):
        """
        Resolve and return the selected view template applied to the object.
        This should not consider the default page.
        """
        template = self.unrestrictedTraverse(self.getLayout())
        return template()

    security.declareProtected(View, 'getDefaultPage')
    def getDefaultPage(self):
        """Return the id of the default page, or None if none is set.

        The default page must be contained within this (folderish) item.
        """
        fti = self.getTypeInfo()
        if fti is None:
            return None
        else:
            plone_utils = getToolByName(self, 'plone_utils', None)
            if plone_utils is not None:
                return plone_utils.getDefaultPage(self)
            else:
                return fti.getDefaultPage(self, check_exists=True)

    security.declareProtected(View, 'getLayout')
    def getLayout(self, **kw):
        """Get the selected view method.

        Note that a selected default page will override the view method.
        """
        fti = self.getTypeInfo()
        if fti is None:
            return None
        else:
            return fti.getViewMethod(self)

    security.declarePublic('canSetDefaultPage')
    def canSetDefaultPage(self):
        """Check if the user has permission to select a default page on this
        (folderish) item, and the item is folderish.
        """
        if not self.isPrincipiaFolderish:
            return False
        mtool = getToolByName(self, 'portal_membership')
        member = mtool.getAuthenticatedMember()
        return member.has_permission(ModifyViewTemplate, self)

    security.declareProtected(ModifyViewTemplate, 'setDefaultPage')
    def setDefaultPage(self, objectId):
        """Set the default page to display in this (folderish) object.

        The objectId must be a value found in self.objectIds() (i.e. a contained
        object). This object will be displayed as the default_page/index_html object
        of this (folderish) object. This will override the current layout
        template returned by getLayout(). Pass None for objectId to turn off
        the default page and return to using the selected layout template.
        """
        new_page = old_page = None
        if objectId is not None:
            new_page = getattr(self, objectId, None)
        if self.hasProperty('default_page'):
            pages = self.getProperty('default_page','')
            if isinstance(pages, (list, tuple)):
                for page in pages:
                    old_page = getattr(self, page, None)
                    if page is not None: break
            elif isinstance(pages, str):
                old_page = getattr(self, pages, None)

            if objectId is None:
                self.manage_delProperties(['default_page'])
            else:
                self.manage_changeProperties(default_page = objectId)
        else:
            if objectId is not None:
                self.manage_addProperty('default_page', objectId, 'string')
        if new_page != old_page:
            if new_page is not None:
                new_page.reindexObject(['is_default_page'])
            if old_page is not None:
                old_page.reindexObject(['is_default_page'])

    security.declareProtected(ModifyViewTemplate, 'setLayout')
    def setLayout(self, layout):
        """Set the layout as the current view.

        'layout' should be one of the list returned by getAvailableLayouts(), but it
        is not enforced. If a default page has been set with setDefaultPage(), it is
        turned off by calling setDefaultPage(None).
        """
        if not (layout and isinstance(layout, basestring)):
            raise ValueError, ("layout must be a non empty string, got %s(%s)" %
                               (layout, type(layout)))

        defaultPage = self.getDefaultPage()
        if defaultPage is None and layout == self.getLayout():
            return

        if self.hasProperty('layout'):
            self.manage_changeProperties(layout = layout)
        else:
            if getattr(aq_base(self), 'layout', _marker) is not _marker:
                # Archetypes remains? clean up
                old = self.layout
                if old and not isinstance(old, basestring):
                    raise RuntimeError, ("layout attribute exists on %s and is"
                                         "no string: %s" % (self, type(old)))
                delattr(self, 'layout')

            self.manage_addProperty('layout', layout, 'string')

        self.setDefaultPage(None)

    security.declareProtected(View, 'getDefaultLayout')
    def getDefaultLayout(self):
        """Get the default layout method.
        """
        fti = self.getTypeInfo()
        if fti is None:
            return "base_view" # XXX
        else:
            return fti.getDefaultViewMethod(self)

    security.declarePublic('canSetLayout')
    def canSetLayout(self):
        """Check if the current authenticated user is permitted to select a layout.
        """
        mtool = getToolByName(self, 'portal_membership')
        member = mtool.getAuthenticatedMember()
        return member.has_permission(ModifyViewTemplate, self)

    security.declareProtected(View, 'getAvailableLayouts')
    def getAvailableLayouts(self):
        """Get the layouts registered for this object from its FTI.
        """
        fti = self.getTypeInfo()
        if fti is None:
            return ()
        result = []
        method_ids = fti.getAvailableViewMethods(self)
        for mid in method_ids:
            view = zope.component.queryMultiAdapter((self, self.REQUEST),
                                                    zope.interface.Interface,
                                                    name=mid)

            if view is not None:
                menu = zope.component.getUtility(
                    IBrowserMenu, 'plone_displayviews')
                item = menu.getMenuItemByAction(self, self.REQUEST, mid)
                title = item and item.title or mid
                result.append((mid, title))
            else:
                method = getattr(self, mid, None)
                if method is not None:
                    # a method might be a template, script or method
                    try:
                        title = method.aq_inner.aq_explicit.title_or_id()
                    except AttributeError:
                        title = mid
                    result.append((mid, title))
        return result

InitializeClass(BrowserDefaultMixin)
