# -*- coding: utf-8 -*-
# $Id$

from zope.interface import implements

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Acquisition import aq_base
from types import ClassType

from Products.CMFCore.TypesTool import FactoryTypeInformation
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName

from Products.CMFDynamicViewFTI.interfaces import IDynamicViewTypeInformation


def safe_hasattr(obj, name, _marker=object()):
    """Make sure we don't mask exceptions like hasattr().

    We don't want exceptions other than AttributeError to be masked,
    since that too often masks other programming errors.
    Three-argument getattr() doesn't mask those, so we use that to
    implement our own hasattr() replacement.
    """
    return getattr(obj, name, _marker) is not _marker


def safe_callable(obj):
    """Make sure our callable checks are ConflictError safe."""
    if safe_hasattr(obj, '__class__'):
        if safe_hasattr(obj, '__call__'):
            return True
        else:
            return isinstance(obj, ClassType)
    else:
        return callable(obj)


def om_has_key(context, key):
    """Object Manager has_key method with optimization for btree folders

    Zope's OFS.ObjectManager has no method for checking if an object with an id
    exists inside a folder.
    """
    klass = getattr(aq_base(context), '__class__', None)
    if hasattr(klass, 'has_key'):
        # BTreeFolder2 optimization
        if context.has_key(key):
            return True
    else:
        # standard ObjectManager api
        if key in context.objectIds():
            return True
    return False

fti_meta_type = 'Factory-based Type Information with dynamic views'

class DynamicViewTypeInformation(FactoryTypeInformation):
    """FTI with dynamic views

    A value of (dynamic view) as alias is replaced by the output of defaultView()
    """

    implements(IDynamicViewTypeInformation)

    meta_type = fti_meta_type
    security = ClassSecurityInfo()

    _properties = FactoryTypeInformation._properties + (
        { 'id': 'default_view', 'type': 'string', 'mode': 'w',
          'label': 'Default view method'
        },
        { 'id': 'view_methods', 'type': 'lines', 'mode': 'w',
          'label': 'Available view methods'
        },
        { 'id': 'default_view_fallback', 'type': 'boolean', 'mode': 'w',
          'label': 'Fall back to default view?'
        },
    )

    default_view = ''
    view_methods = ()
    default_view_fallback = False

    def manage_changeProperties(self, **kw):
        """Overwrite change properties to verify that default_view is in the method
        list
        """
        FactoryTypeInformation.manage_changeProperties(self, **kw)
        default_view = self.default_view
        view_methods = self.view_methods
        if not default_view:
            # TODO: use view action
            self.default_view = default_view = self.immediate_view
        if not view_methods:
            self.view_methods = view_methods = (default_view,)
        if default_view and default_view not in view_methods:
            raise ValueError, "%s not in %s" % (default_view, view_methods)

    security.declareProtected(View, 'getDefaultViewMethod')
    def getDefaultViewMethod(self, context):
        """Get the default view method from the FTI
        """
        return str(self.default_view)

    security.declareProtected(View, 'getAvailableViewMethods')
    def getAvailableViewMethods(self, context):
        """Get a list of registered view methods
        """
        methods = self.view_methods
        if isinstance(methods, basestring):
            methods = (methods,)
        return tuple(methods)

    security.declareProtected(View, 'getViewMethod')
    def getViewMethod(self, context, enforce_available=False, check_exists=False):
        """Get view method (aka layout) name from context

        Return -- view method from context or default view name
        """
        default = self.getDefaultViewMethod(context)
        layout = getattr(aq_base(context), 'layout', None)

        if safe_callable(layout):
            layout = layout()
        if not layout:
            return default
        if not isinstance(layout, basestring):
            raise TypeError, "layout of %s must be a string, got %s" % (
                              repr(context), type(layout))
        if enforce_available:
            available = self.getAvailableViewMethods(context)
            if layout not in available:
                return default
        if check_exists:
            method = getattr(context, layout, None)
            if method is None:
                return default
        return layout

    security.declareProtected(View, 'getDefaultPage')
    def getDefaultPage(self, context, check_exists=False):
        """Get the default page from a folderish object

        Non folderish objects don't have a default view.

        If check_exists is enabled the method makes sure the object with the default
        page id exists.

        Return -- None for no default page or a string
        """
        if not getattr(aq_base(context), 'isPrincipiaFolderish', False):
            return None # non folderish objects don't have a default page per se

        default_page = getattr(aq_base(context), 'default_page', None)

        if safe_callable(default_page):
            default_page = default_page()
        if not default_page:
            return None
        if isinstance(default_page, (tuple, list)):
            default_page = default_page[0]
        if not isinstance(default_page, str):
            raise TypeError, ("default_page must be a string, got %s(%s):" %
                              (default_page, type(default_page)))

        if check_exists and not om_has_key(context, default_page):
            return None

        return default_page

    security.declareProtected(View, 'defaultView')
    def defaultView(self, context):
        """Get the current view to use for an object. If a default page is  set,
        use that, else use the currently selected view method/layout.
        """

        # Delegate to PloneTool's version if we have it else, use own rules
        plone_utils = getToolByName(self, 'plone_utils', None)
        if plone_utils is not None:
            obj, path = plone_utils.browserDefault(context)
            return path[-1]
        else:
            default_page = self.getDefaultPage(context, check_exists=True)
            if default_page is not None:
                return default_page
            fallback = self.default_view_fallback
            return self.getViewMethod(context, check_exists=fallback)

    security.declarePublic('queryMethodID')
    def queryMethodID(self, alias, default=None, context=None):
        """ Query method ID by alias.

        Use "(dynamic view)" as the alias target to look up as per defaultView()
        Use "(selected layout)" as the alias target to look up as per
            getViewMethod()
        """
        methodTarget = FactoryTypeInformation.queryMethodID(self, alias,
                                                         default=default,
                                                         context=context)
        if not isinstance(methodTarget, basestring):
            # nothing to do, method_id is probably None
            return methodTarget

        if context is None or default == '':
            # the edit zpts like typesAliases don't apply a context and set the
            # default to ''. We do not want to resolve (dynamic view) for these
            # methods.
            return methodTarget

        # Our two special targets:

        if methodTarget.lower() == "(dynamic view)":
            methodTarget = self.defaultView(context)

        if methodTarget.lower() == "(selected layout)":
            fallback = self.default_view_fallback
            methodTarget = self.getViewMethod(context, check_exists=fallback)

        return methodTarget

InitializeClass(DynamicViewTypeInformation)
