##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Information about customizable actions. """

from UserDict import UserDict

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base, aq_inner, aq_parent
from App.class_init import InitializeClass
from OFS.ObjectManager import IFAwareObjectManager
from OFS.OrderedFolder import OrderedFolder
from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import SimpleItem
from zope.i18nmessageid import Message
from zope.interface import implements

from Products.CMFCore.Expression import Expression
from Products.CMFCore.interfaces import IAction
from Products.CMFCore.interfaces import IActionCategory
from Products.CMFCore.interfaces import IActionInfo
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import getToolByName

_unchanged = [] # marker


class ActionCategory(IFAwareObjectManager, OrderedFolder):

    """ Group of Action objects.
    """

    implements(IActionCategory)

    _product_interfaces = (IActionCategory, IAction)

    security = ClassSecurityInfo()

    security.declarePrivate('listActions')
    def listActions(self):
        """ List the actions defined in this category and its subcategories.
        """
        actions = []

        for obj in self.objectValues():
            if IActionCategory.providedBy(obj):
                actions.extend( obj.listActions() )
            elif IAction.providedBy(obj):
                actions.append(obj)

        return tuple(actions)

InitializeClass(ActionCategory)


class Action(PropertyManager, SimpleItem):

    """ Reference to an action.
    """

    implements(IAction)

    i18n_domain = 'cmf_default'
    link_target = ''

    security = ClassSecurityInfo()

    _properties = (
        {'id': 'title', 'type': 'string', 'mode': 'w',
         'label': 'Title'},
        {'id': 'description', 'type': 'text', 'mode': 'w',
         'label': 'Description'},
        {'id':'i18n_domain', 'type': 'string', 'mode':'w',
         'label':'I18n Domain'},
        {'id': 'url_expr', 'type': 'string', 'mode': 'w',
         'label': 'URL (Expression)'},
        {'id':'link_target', 'type': 'string', 'mode':'w',
         'label':'Link Target'},
        {'id': 'icon_expr', 'type': 'string', 'mode': 'w',
         'label': 'Icon (Expression)'},
        {'id': 'available_expr', 'type': 'string', 'mode': 'w',
         'label': 'Condition (Expression)'},
        {'id': 'permissions', 'type': 'multiple selection', 'mode': 'w',
         'label': 'Permissions', 'select_variable': 'possible_permissions'},
        {'id': 'visible', 'type': 'boolean', 'mode': 'w',
         'label': 'Visible?'},
        )

    manage_options = (
        PropertyManager.manage_options
        + SimpleItem.manage_options)

    def __init__(self, id, **kw):
        self.id = id
        self._setPropValue( 'title', kw.get('title', '') )
        self._setPropValue( 'description', kw.get('description', '') )
        self._setPropValue( 'i18n_domain', kw.get('i18n_domain', '') )
        self._setPropValue( 'url_expr', kw.get('url_expr', '') )
        self._setPropValue( 'link_target', kw.get('link_target', '') )
        self._setPropValue( 'icon_expr', kw.get('icon_expr', '') )
        self._setPropValue( 'available_expr', kw.get('available_expr', '') )
        self._setPropValue( 'permissions', kw.get('permissions', () ) )
        self._setPropValue( 'visible', kw.get('visible', True) )

    def _setPropValue(self, id, value):
        self._wrapperCheck(value)
        if isinstance(value, list):
            value = tuple(value)
        setattr(self, id, value)
        if id.endswith('_expr'):
            attr = '%s_object' % id
            if value:
                setattr(self, attr, Expression(value))
            elif hasattr(self, attr):
                delattr(self, attr)

    security.declarePrivate('getInfoData')
    def getInfoData(self):
        """ Get the data needed to create an ActionInfo.
        """
        category_path = []
        lazy_keys = []
        lazy_map = {}

        lazy_map['id'] = self.getId()

        parent = aq_parent(self)
        while parent is not None and parent.getId() != 'portal_actions':
            category_path.append( parent.getId() )
            parent = aq_parent(parent)
        lazy_map['category'] = '/'.join(category_path[::-1])

        for id, val in self.propertyItems():
            if id.endswith('_expr'):
                id = id[:-5]
                if val:
                    val = getattr(self, '%s_expr_object' % id)
                    lazy_keys.append(id)
                elif id == 'available':
                    val = True
            elif id == 'i18n_domain':
                continue
            elif id == 'link_target':
                val = val or None
            elif self.i18n_domain and id in ('title', 'description'):
                val = Message(val, self.i18n_domain)
            lazy_map[id] = val

        return (lazy_map, lazy_keys)

InitializeClass(Action)


class ActionInfo(UserDict):

    """ A lazy dictionary for Action infos.
    """

    implements(IActionInfo)

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, action, ec):

        if isinstance(action, dict):
            lazy_keys = []
            UserDict.__init__(self, action)
            if 'name' in self.data:
                self.data.setdefault( 'id', self.data['name'].lower() )
                self.data.setdefault( 'title', self.data['name'] )
                del self.data['name']
            self.data.setdefault( 'url', '' )
            self.data.setdefault( 'link_target', None )
            self.data.setdefault( 'icon', '' )
            self.data.setdefault( 'category', 'object' )
            self.data.setdefault( 'visible', True )
            self.data['available'] = True
        else:
            # if action isn't a dict, it has to implement IAction
            (lazy_map, lazy_keys) = action.getInfoData()
            UserDict.__init__(self, lazy_map)

        self.data.setdefault('allowed', True)
        permissions = self.data.pop( 'permissions', () )
        if permissions:
            self.data['allowed'] = self._checkPermissions
            lazy_keys.append('allowed')

        self._ec = ec
        self._lazy_keys = lazy_keys
        self._permissions = permissions

    def __getitem__(self, key):
        value = UserDict.__getitem__(self, key)
        if key in self._lazy_keys:
            value = self.data[key] = value(self._ec)
            self._lazy_keys.remove(key)
        return value

    def __eq__(self, other):
        # this is expensive, use it with care
        [ self.__getitem__(key) for key in self._lazy_keys[:] ]

        if isinstance(other, self.__class__):
            [ other[key] for key in other._lazy_keys ]
            return self.data == other.data
        elif isinstance(other, UserDict):
            return self.data == other.data
        else:
            return self.data == other

    def copy(self):
        c = UserDict.copy(self)
        c._lazy_keys = self._lazy_keys[:]
        return c

    def _checkPermissions(self, ec):
        """ Check permissions in the current context.
        """
        category = self['category']
        object = ec.contexts['object']
        if object is not None and ( category.startswith('object') or
                                    category.startswith('workflow') or
                                    category.startswith('document') ):
            context = object
        else:
            folder = ec.contexts['folder']
            if folder is not None and category.startswith('folder'):
                context = folder
            else:
                context = ec.contexts['portal']

        for permission in self._permissions:
            if _checkPermission(permission, context):
                return True
        return False


class ActionInformation( SimpleItem ):

    """ Represent a single selectable action.

    Actions generate links to views of content, or to specific methods
    of the site.  They can be filtered via their conditions.
    """

    implements(IAction)

    link_target = ''

    __allow_access_to_unprotected_subobjects__ = 1

    security = ClassSecurityInfo()

    def __init__( self
                , id
                , title=''
                , description=''
                , category='object'
                , condition=''
                , permissions=()
                , priority=10
                , visible=True
                , action=''
                , icon_expr=''
                , link_target=''
                ):
        """ Set up an instance.
        """
        self.edit( id
                 , title
                 , description
                 , category
                 , condition
                 , permissions
                 , priority
                 , visible
                 , action
                 , icon_expr
                 , link_target
                 )

    security.declarePrivate('edit')
    def edit( self
            , id=_unchanged
            , title=_unchanged
            , description=_unchanged
            , category=_unchanged
            , condition=_unchanged
            , permissions=_unchanged
            , priority=_unchanged
            , visible=_unchanged
            , action=_unchanged
            , icon_expr=_unchanged
            , link_target=_unchanged
            ):
        """Edit the specified properties.
        """

        if id is not _unchanged:
            self.id = id
        if title is not _unchanged:
            self.title = title
        if description is not _unchanged:
            self.description = description
        if category is not _unchanged:
            self.category = category
        if condition is not _unchanged:
            if condition and isinstance(condition, basestring):
                condition = Expression(condition)
            self.condition = condition
        if permissions is not _unchanged:
            if permissions == ('',):
                permissions = ()
            self.permissions = permissions
        if priority is not _unchanged:
            self.priority = priority
        if visible is not _unchanged:
            self.visible = visible
        if action is not _unchanged:
            if action and isinstance(action, basestring):
                action = Expression(action)
            self.setActionExpression(action)
        if icon_expr is not _unchanged:
            if icon_expr and isinstance(icon_expr, basestring):
                icon_expr = Expression(icon_expr)
            self.setIconExpression(icon_expr)
        if link_target is not _unchanged:
            self.link_target = link_target

    security.declareProtected( View, 'Title' )
    def Title(self):

        """ Return the Action title.
        """
        return self.title or self.getId()

    security.declareProtected( View, 'Description' )
    def Description( self ):

        """ Return a description of the action.
        """
        return self.description

    security.declarePrivate( 'testCondition' )
    def testCondition( self, ec ):

        """ Evaluate condition using context, 'ec', and return 0 or 1.
        """
        if self.condition:
            return bool( self.condition(ec) )
        else:
            return True

    security.declarePublic( 'getAction' )
    def getAction( self, ec ):

        """ Compute the action using context, 'ec'; return a mapping of
            info about the action.
        """
        return ActionInfo(self, ec)

    security.declarePrivate( '_getActionObject' )
    def _getActionObject( self ):

        """ Find the action object, working around name changes.
        """
        action = getattr( self, 'action', None )

        if action is None:  # Forward compatibility, used to be '_action'
            action = getattr( self, '_action', None )
            if action is not None:
                self.action = self._action
                del self._action

        return action

    security.declarePublic( 'getActionExpression' )
    def getActionExpression( self ):

        """ Return the text of the TALES expression for our URL.
        """
        action = self._getActionObject()
        expr = action and action.text or ''
        if expr and isinstance(expr, basestring):
            if ( not expr.startswith('string:')
                 and not expr.startswith('python:') ):
                expr = 'string:${object_url}/%s' % expr
                self.action = Expression( expr )
        return expr

    security.declarePrivate( 'setActionExpression' )
    def setActionExpression(self, action):
        if action and isinstance(action, basestring):
            if ( not action.startswith('string:')
                 and not action.startswith('python:') ):
                action = 'string:${object_url}/%s' % action
            action = Expression( action )
        self.action = action

    security.declarePrivate( '_getIconExpressionObject' )
    def _getIconExpressionObject( self ):

        """ Find the icon expression object, working around name changes.
        """
        return getattr( self, 'icon_expr', None )

    security.declarePublic( 'getIconExpression' )
    def getIconExpression( self ):

        """ Return the text of the TALES expression for our icon URL.
        """
        icon_expr = self._getIconExpressionObject()
        expr = icon_expr and icon_expr.text or ''
        if expr and isinstance(expr, basestring):
            if ( not expr.startswith('string:')
                 and not expr.startswith('python:') ):
                expr = 'string:${object_url}/%s' % expr
                self.icon_expr = Expression( expr )
        return expr

    security.declarePrivate( 'setIconExpression' )
    def setIconExpression(self, icon_expr):
        if icon_expr and isinstance(icon_expr, basestring):
            if ( not icon_expr.startswith('string:')
                 and not icon_expr.startswith('python:') ):
                icon_expr = 'string:${object_url}/%s' % icon_expr
            icon_expr = Expression( icon_expr )
        self.icon_expr = icon_expr

    security.declarePublic( 'getCondition' )
    def getCondition(self):

        """ Return the text of the TALES expression for our condition.
        """
        return getattr( self, 'condition', None ) and self.condition.text or ''

    security.declarePublic( 'getPermissions' )
    def getPermissions( self ):

        """ Return the permission, if any, required to execute the action.

        Return an empty tuple if no permission is required.
        """
        return self.permissions

    security.declarePublic( 'getCategory' )
    def getCategory( self ):

        """ Return the category in which the action should be grouped.
        """
        return self.category or 'object'

    security.declarePublic( 'getVisibility' )
    def getVisibility( self ):

        """ Return whether the action should be visible in the CMF UI.
        """
        return bool(self.visible)

    security.declarePublic('getLinkTarget')
    def getLinkTarget(self):
        """ Return the rendered link tag's target attribute value
        """
        return self.link_target

    security.declarePrivate('getMapping')
    def getMapping(self):
        """ Get a mapping of this object's data.
        """
        return { 'id': self.id,
                 'title': self.title or self.id,
                 'description': self.description,
                 'category': self.category or 'object',
                 'condition': getattr(self, 'condition', None)
                              and self.condition.text or '',
                 'permissions': self.permissions,
                 'visible': bool(self.visible),
                 'action': self.getActionExpression(),
                 'icon_expr' : self.getIconExpression(),
                 'link_target' : self.getLinkTarget() }

    security.declarePrivate('clone')
    def clone( self ):
        """ Get a newly-created AI just like us.
        """
        return self.__class__( priority=self.priority, **self.getMapping() )

    security.declarePrivate('getInfoData')
    def getInfoData(self):
        """ Get the data needed to create an ActionInfo.
        """
        lazy_keys = []
        lazy_map = self.getMapping()

        if not lazy_map['link_target']:
            lazy_map['link_target'] = None

        if lazy_map['action']:
            lazy_map['url'] = self._getActionObject()
            lazy_keys.append('url')
        else:
            lazy_map['url'] = ''
        del lazy_map['action']

        if lazy_map['icon_expr']:
            lazy_map['icon'] = self._getIconExpressionObject()
            lazy_keys.append('icon')
        else:
            lazy_map['icon'] = ''
        del lazy_map['icon_expr']

        if lazy_map['condition']:
            lazy_map['available'] = self.testCondition
            lazy_keys.append('available')
        else:
            lazy_map['available'] = True
        del lazy_map['condition']

        return (lazy_map, lazy_keys)

InitializeClass( ActionInformation )


def getOAI(context, object=None):
    request = getattr(context, 'REQUEST', None)
    if request:
        cache = request.get('_oai_cache', None)
        if cache is None:
            request['_oai_cache'] = cache = {}
        info = cache.get( id(object), None )
    else:
        info = None
    if info is None:
        if object is None or not hasattr(object, 'aq_base'):
            folder = None
        else:
            folder = object
            # Search up the containment hierarchy until we find an
            # object that claims it's a folder.
            while folder is not None:
                if getattr(aq_base(folder), 'isPrincipiaFolderish', 0):
                    # found it.
                    break
                else:
                    folder = aq_parent(aq_inner(folder))
        info = oai(context, folder, object)
        if request:
            cache[ id(object) ] = info
    return info


class oai:

    #Provided for backwards compatability
    # Provides information that may be needed when constructing the list of
    # available actions.
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__( self, tool, folder, object=None ):
        self.portal = portal = aq_parent(aq_inner(tool))
        membership = getToolByName(tool, 'portal_membership')
        self.isAnonymous = membership.isAnonymousUser()
        self.user_id = membership.getAuthenticatedMember().getId()
        self.portal_url = portal.absolute_url()
        if folder is not None:
            self.folder_url = folder.absolute_url()
            self.folder = folder
        else:
            self.folder_url = self.portal_url
            self.folder = portal

        # The name "content" is deprecated and will go away in CMF 2.0!
        self.object = self.content = object
        if object is not None:
            self.content_url = self.object_url = object.absolute_url()
        else:
            self.content_url = self.object_url = None

    def __getitem__(self, name):
        # Mapping interface for easy string formatting.
        if name[:1] == '_':
            raise KeyError, name
        if hasattr(self, name):
            return getattr(self, name)
        raise KeyError, name
