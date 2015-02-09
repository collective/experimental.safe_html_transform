##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Portal class """

from App.class_init import InitializeClass

from Products.CMFCore.PortalObject import PortalObjectBase
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFDefault.permissions import AddPortalContent
from Products.CMFDefault.permissions import AddPortalFolders
from Products.CMFDefault.permissions import ListPortalMembers
from Products.CMFDefault.permissions import ReplyToItem
from Products.CMFDefault.permissions import View


class CMFSite(PortalObjectBase, DefaultDublinCoreImpl):

    """
        The *only* function this class should have is to help in the setup
        of a new CMFSite.  It should not assist in the functionality at all.
    """
    meta_type = 'CMF Site'

    _properties = (
        {'id':'title', 'type':'string', 'mode': 'w'},
        {'id':'description', 'type':'text', 'mode': 'w'},
        )
    title = ''
    description = ''

    __ac_permissions__=( ( AddPortalContent, () )
                       , ( AddPortalFolders, () )
                       , ( ListPortalMembers, () )
                       , ( ReplyToItem, () )
                       , ( View, ('isEffective',) )
                       )

    def __init__( self, id, title='' ):
        PortalObjectBase.__init__( self, id, title )
        DefaultDublinCoreImpl.__init__( self )

    def isEffective( self, date ):
        """
            Override DefaultDublinCoreImpl's test, since we are always viewable.
        """
        return 1

    def reindexObject( self, idxs=[] ):
        """
            Override DefaultDublinCoreImpl's method (so that we can play
            in 'editMetadata').
        """
        pass

InitializeClass(CMFSite)
