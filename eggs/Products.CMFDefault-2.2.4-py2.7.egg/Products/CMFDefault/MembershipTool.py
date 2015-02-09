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
""" CMFDefault portal_membership tool. """

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from zope.interface import implements

from Products.CMFCore.MembershipTool import MembershipTool as BaseTool
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFDefault.Document import addDocument
from Products.CMFDefault.interfaces import IMembershipTool
from Products.CMFDefault.permissions import ListPortalMembers
from Products.CMFDefault.permissions import ManagePortal
from Products.CMFDefault.permissions import ManageUsers
from Products.CMFDefault.permissions import View
from Products.CMFDefault.utils import _dtmldir

DEFAULT_MEMBER_CONTENT = """\
Default page for %s

  This is the default document created for you when
  you joined this community.

  To change the content just select "Edit"
  in the Tool Box on the left.
"""


class MembershipTool(BaseTool):

    """ Implement 'portal_membership' interface using "stock" policies.
    """

    implements(IMembershipTool)

    meta_type = 'Default Membership Tool'
    membersfolder_id = 'Members'

    security = ClassSecurityInfo()

    #
    #   ZMI methods
    #
    security.declareProtected( ManagePortal, 'manage_overview' )
    manage_overview = DTMLFile( 'explainMembershipTool', _dtmldir )

    security.declareProtected(ManagePortal, 'manage_mapRoles')
    manage_mapRoles = DTMLFile('membershipRolemapping', _dtmldir )

    security.declareProtected(ManagePortal, 'manage_setMembersFolderById')
    def manage_setMembersFolderById(self, id='', REQUEST=None):
        """ ZMI method to set the members folder object by its id.
        """
        self.setMembersFolderById(id)
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect( self.absolute_url()
                    + '/manage_mapRoles'
                    + '?manage_tabs_message=Members+folder+changed.'
                    )

    #
    #   'portal_membership' interface methods
    #
    security.declareProtected( ListPortalMembers, 'getRoster' )
    def getRoster(self):
        """ Return a list of mappings for 'listed' members.

        If Manager, return a list of all usernames.  The mapping
        contains the id and listed variables.
        """
        isUserManager = _checkPermission(ManageUsers, self)
        roster = []
        for member in self.listMembers():
            if isUserManager or member.listed:
                roster.append({'id':member.getId(),
                               'listed':member.listed})
        return roster

    security.declareProtected(ManagePortal, 'setMembersFolderById')
    def setMembersFolderById(self, id=''):
        """ Set the members folder object by its id.
        """
        self.membersfolder_id = id.strip()

    security.declarePublic('getMembersFolder')
    def getMembersFolder(self):
        """ Get the members folder object.
        """
        parent = aq_parent( aq_inner(self) )
        try:
            members_folder = parent.restrictedTraverse(self.membersfolder_id)
        except (AttributeError, KeyError):
            members_folder = None
        return members_folder

    security.declarePublic('createMemberArea')
    def createMemberArea(self, member_id=''):
        """ Create a member area for 'member_id' or authenticated user.
        """
        if not self.getMemberareaCreationFlag():
            return None
        members = self.getMembersFolder()
        if members is None:
            return None
        if self.isAnonymousUser():
            return None
        # Note: We can't use getAuthenticatedMember() and getMemberById()
        # because they might be wrapped by MemberDataTool.
        user = _getAuthenticatedUser(self)
        user_id = user.getId()
        if member_id in ('', user_id):
            member = user
            member_id = user_id
        else:
            if _checkPermission(ManageUsers, self):
                member = self.acl_users.getUserById(member_id, None)
                if member:
                    member = member.__of__(self.acl_users)
                else:
                    raise ValueError, 'Member %s does not exist' % member_id
            else:
                return None
        if hasattr( aq_base(members), member_id ):
            return None

        # Note: We can't use invokeFactory() to add folder and content because
        # the user might not have the necessary permissions.

        # Create Member's home folder.
        members.manage_addPortalFolder(id=member_id,
                                       title="%s's Home" % member_id)
        f = members._getOb(member_id)

        # Grant Ownership and Owner role to Member
        f.changeOwnership(member)
        f.__ac_local_roles__ = None
        f.manage_setLocalRoles(member_id, ['Owner'])

        # Create Member's initial content.
        if hasattr(self, 'createMemberContent'):
            self.createMemberContent(member=member,
                                   member_id=member_id,
                                   member_folder=f)
        else:
            addDocument( f
                       , 'index_html'
                       , member_id+"'s Home"
                       , member_id+"'s front page"
                       , "structured-text"
                       , (DEFAULT_MEMBER_CONTENT % member_id)
                       )

            # Grant Ownership and Owner role to Member
            f.index_html.changeOwnership(member)
            f.index_html.__ac_local_roles__ = None
            f.index_html.manage_setLocalRoles(member_id, ['Owner'])

            f.index_html._setPortalTypeName( 'Document' )
            f.index_html.reindexObject()
            f.index_html.notifyWorkflowCreated()
        return f

    security.declarePublic('createMemberarea')
    createMemberarea = createMemberArea

    def getHomeFolder(self, id=None, verifyPermission=0):
        """ Return a member's home folder object, or None.
        """
        if id is None:
            member = self.getAuthenticatedMember()
            if not hasattr(member, 'getMemberId'):
                return None
            id = member.getMemberId()
        members = self.getMembersFolder()
        if members:
            try:
                folder = members._getOb(id)
                if verifyPermission and not _checkPermission(View, folder):
                    # Don't return the folder if the user can't get to it.
                    return None
                return folder
            except (AttributeError, TypeError, KeyError):
                pass
        return None

    def getHomeUrl(self, id=None, verifyPermission=0):
        """ Return the URL to a member's home folder, or None.
        """
        home = self.getHomeFolder(id, verifyPermission)
        if home is not None:
            return home.absolute_url()
        else:
            return None

InitializeClass(MembershipTool)
