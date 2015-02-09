##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Map CMF actions to icons, for ease of building icon-centric toolbars.

$Id: ActionIconsTool.py 110650 2010-04-08 15:30:52Z tseaver $
"""

import os

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from App.Common import package_home
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.interface import implements

from Products.CMFActionIcons.interfaces import IActionIconsTool
from Products.CMFActionIcons.permissions import ManagePortal
from Products.CMFActionIcons.permissions import View
from Products.CMFCore.Expression import Expression
from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import UniqueObject

_wwwdir = os.path.join( package_home( globals() ), 'www' )


class ActionIcon( SimpleItem ):

    security = ClassSecurityInfo()

    _title = None           # Use the one supplied by the provider
    _priority = 0           # All animals are equal....
    _category = 'object'
    _action_id = 'view'
    _icon_expr_text = 'document_icon'

    def __init__( self
                , category
                , action_id
                , icon_expr_text=''
                , title=None
                , priority=0
                ):

        self._category = category
        self._action_id = action_id
        self.updateIconExpression( icon_expr_text )
        self._title = title
        self._priority = priority

    security.declareProtected( View, 'getTitle' )
    def getTitle( self ):

        """ Simple accessor """
        return self._title

    security.declareProtected( View, 'getPriority' )
    def getPriority( self ):

        """ Simple accessor """
        return self._priority

    security.declareProtected( View, 'getCategory' )
    def getCategory( self ):

        """ Simple accessor """
        return self._category

    security.declareProtected( View, 'getActionId' )
    def getActionId( self ):

        """ Simple accessor """
        return self._action_id

    security.declareProtected( View, 'getExpression' )
    def getExpression( self ):

        """ Simple accessor """
        return self._icon_expr_text

    security.declareProtected( View, 'getIconURL' )
    def getIconURL( self, context=None ):

        """ Simple accessor """
        if context is None:
            return self._icon_expr_text

        return self._icon_expr( context )

    security.declareProtected( ManagePortal, 'updateIconExpression' )
    def updateIconExpression( self, icon_expr_text ):

        """ Mutate icon expression. """
        self._icon_expr_text = icon_expr_text

        if not ':' in icon_expr_text: # default to 'string:' type
            icon_expr_text = 'string:%s' % icon_expr_text

        self._icon_expr = Expression( icon_expr_text )

InitializeClass( ActionIcon )


class ActionIconsTool( UniqueObject, SimpleItem ):

    """ Map actions only icons.
    """

    implements(IActionIconsTool)

    meta_type = 'Action Icons Tool'
    id = 'portal_actionicons'

    security = ClassSecurityInfo()
    security.declareObjectProtected( View )

    def __init__( self ):

        self.clearActionIcons()

    #
    #   Accessors
    #
    security.declareProtected( ManagePortal, 'listActionIcons' )
    def listActionIcons( self ):

        """ Return a sequence of mappings for action icons

        o Mappings are in the form: ( category, action ) -> icon,
          where category and action are strings and icon is an ActionIcon
          instance.
        """
        return [ x.__of__( self ) for x in self._icons ]

    security.declareProtected( View, 'getActionInfo' )
    def getActionInfo( self
                     , category
                     , action_id
                     , context=None
                     ):

        """ Return a tuple, '(title, priority, icon ID), for the given action.

        o Raise a KeyError if no icon has been defined for the action.
        """
        ai = self._lookup[ ( category, action_id ) ]
        return ( ai.getTitle()
               , ai.getPriority()
               , ai.getIconURL( context )
               )

    security.declareProtected( View, 'queryActionInfo' )
    def queryActionInfo( self
                       , category
                       , action_id
                       , default=None
                       , context=None
                       ):

        """ Return a tuple, '(title, priority, icon ID), for the given action.

        o Return 'default' if no icon has been defined for the action.
        """
        ai = self._lookup.get( ( category, action_id ) )
        return ai and ( ai.getTitle()
                      , ai.getPriority()
                      , ai.getIconURL( context )
                      ) or default

    security.declareProtected( View, 'getActionIcon' )
    def getActionIcon( self, category, action_id, context=None ):

        """ Return an icon ID for the given action.

        o Raise a KeyError if no icon has been defined for the action.

        o Context is an Expression context object, used to evaluate
          TALES expressions.
        """
        return self._lookup[ ( category, action_id ) ].getIconURL( context )

    security.declareProtected( View, 'queryActionIcon' )
    def queryActionIcon( self, category, action_id
                       , default=None, context=None ):

        """ Return an icon ID for the given action.

        o Return 'default' if no icon has been defined for the action.

        o Context is an Expression context object, used to evaluate
          TALES expressions.
        """
        ai = self._lookup.get( ( category, action_id ) )
        return ai and ai.getIconURL( context ) or default

    security.declareProtected( View, 'updateActionDicts' )
    def updateActionDicts( self, categorized_actions, context=None ):

        """ Update a set of dictionaries, adding 'title, 'priority', and
            'icon' keys.

        o S.b. passed a data structure like that returned from ActionsTool's
          'listFilteredActionsFor':

          - Dict mapping category -> seq. of dicts, where each of the
            leaf dicts must have 'category' and 'id' keys.

        o *Will* overwrite the 'title' key, if title is defined on the tool.

        o *Will* overwrite the 'priority' key.

        o *Will* overwrite the 'icon' key, if icon is defined on the tool

        o XXX:  Don't have a way to pass Expression context yet.
        """
        result = {}

        for category, actions in categorized_actions.items():

            new_actions = []

            for action in actions:

                action = action.copy()

                action_id = action.get( 'id' )

                #  Hack around DCWorkflow's ID-less worklist actions.
                if action_id is None and action.get( 'category' ) == 'workflow':
                    action[ 'id' ] = action_id = action.get( 'name' )

                if action_id:

                    info = self.queryActionInfo( category
                                               , action_id
                                               , context=context
                                               )
                    if info is not None:

                        title, priority, icon = info

                        if title is not None:
                            action[ 'title' ] = title

                        if priority is not None:
                            action[ 'priority' ] = priority

                        if icon is not None:
                            action[ 'icon' ] = icon

                new_actions.append( action )

            new_actions.sort( lambda x, y: cmp( x.get( 'priority', 0 )
                                              , y.get( 'priority', 0 )
                                              ) )
            result[ category ] = new_actions

        return result

    __call__ = updateActionDicts

    #
    #   Mutators
    #
    security.declareProtected( ManagePortal, 'addActionIcon' )
    def addActionIcon( self
                     , category
                     , action_id
                     , icon_expr
                     , title=None
                     , priority=0
                     ):

        """ Add an icon for the given action.

        o Raise KeyError if an icon has already been defined.
        """
        if self.queryActionInfo( category, action_id ) is not None:
            raise KeyError, 'Duplicate definition!'

        icons = list( self._icons )
        icons.append( ActionIcon( category
                                , action_id
                                , icon_expr
                                , title
                                , priority
                                ) )
        self._lookup[ ( category, action_id ) ] = icons[-1]
        self._icons = tuple( icons )

    security.declareProtected( ManagePortal, 'updateActionIcon' )
    def updateActionIcon( self
                        , category
                        , action_id
                        , icon_expr
                        , title=None
                        , priority=0
                        ):

        """ Update the icon for the given action.

        o Raise KeyError if an icon has not already been defined.
        """
        if self._lookup.get( ( category, action_id ) ) is None:
            raise KeyError, 'No such definition!'

        icons = list( self._icons )
        for ai in icons:
            if ( ai.getCategory() == category
             and ai.getActionId() == action_id
               ):
                ai.updateIconExpression( icon_expr )
                ai._title = title
                ai._priority = priority
                break
        else:
            raise KeyError, ( category, action_id )
        self._icons = tuple( icons )

    security.declareProtected( ManagePortal, 'removeActionIcon' )
    def removeActionIcon( self, category, action_id ):

        """ Remove the icon for the given action.

        o Raise KeyError if an icon has not already been defined.
        """
        if self.queryActionInfo( category, action_id ) is None:
            raise KeyError, 'No such definition (%s, %s)!' % (
                category, action_id)

        icons = list( self._icons )
        icon = self._lookup[ ( category, action_id ) ]
        icons.remove( icon )
        del self._lookup[ ( category, action_id ) ]
        self._icons = tuple( icons )

    security.declareProtected( ManagePortal, 'clearActionIcons' )
    def clearActionIcons( self ):

        """ Remove all mappings from the tool.
        """
        self._icons = ()
        self._lookup = {}

    #
    #   ZMI
    #
    manage_options =  ( { 'label' : 'Icons'
                        , 'action' : 'manage_editActionIcons'
                        }
                      ,
                      ) + SimpleItem.manage_options

    security.declareProtected( ManagePortal, 'manage_editActionIcons' )
    manage_editActionIcons = PageTemplateFile( 'aitEdit', _wwwdir )

    security.declareProtected( ManagePortal, 'manage_addActionIcon' )
    def manage_addActionIcon( self
                            , category
                            , action_id
                            , icon_expr
                            , title
                            , priority
                            , REQUEST
                            ):

        """ Add an icon for the given action via the ZMI.
        """
        self.addActionIcon( category
                          , action_id
                          , icon_expr
                          , title
                          , priority
                          )

        REQUEST['RESPONSE'].redirect( '%s/manage_editActionIcons'
                                      '?manage_tabs_message=Action+added.'
                                    % self.absolute_url()
                                    )

    security.declareProtected( ManagePortal, 'manage_updateActionIcon' )
    def manage_updateActionIcon( self
                               , category
                               , action_id
                               , icon_expr
                               , title
                               , priority
                               , REQUEST
                               ):

        """ Update an icon for the given action via the ZMI.
        """
        self.updateActionIcon( category
                             , action_id
                             , icon_expr
                             , title
                             , priority
                             )

        REQUEST['RESPONSE'].redirect( '%s/manage_editActionIcons'
                                      '?manage_tabs_message=Action+updated.'
                                    % self.absolute_url()
                                    )

    security.declareProtected( ManagePortal, 'manage_removeActionIcon' )
    def manage_removeActionIcon( self, category, action_id, REQUEST ):

        """ Remove the icon for the given action via the ZMI.
        """
        self.removeActionIcon( category, action_id )

        REQUEST['RESPONSE'].redirect( '%s/manage_editActionIcons'
                                      '?manage_tabs_message=Action+removed.'
                                    % self.absolute_url()
                                    )

InitializeClass( ActionIconsTool )
registerToolInterface('portal_actionicons', IActionIconsTool)
