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
""" CMFDefault portal_registration tool. """

from warnings import warn

from AccessControl.requestmethod import postonly
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from Products.MailHost.interfaces import IMailHost
from zope.component import getUtility
from zope.schema import ValidationError

from Products.CMFCore.RegistrationTool import RegistrationTool as BaseTool
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.permissions import ManagePortal
from Products.CMFDefault.utils import checkEmailAddress
from Products.CMFDefault.utils import Message as _


class RegistrationTool(BaseTool):

    """ Manage through-the-web signup policies.
    """

    meta_type = 'Default Registration Tool'

    security = ClassSecurityInfo()

    def _getValidEmailAddress(self, member):
        email = member.getProperty('email')

        # assert that we can actually get an email address, otherwise
        # the template will be made with a blank To:, this is bad
        if email is None:
            msg = _(u'No email address is registered for member: '
                    u'${member_id}', mapping={'member_id': member.getId()})
            raise ValueError(msg)

        checkEmailAddress(email)
        return email

    #
    #   'portal_registration' interface
    #
    security.declarePublic( 'testPasswordValidity' )
    def testPasswordValidity(self, password, confirm=None):

        """ Verify that the password satisfies the portal's requirements.

        o If the password is valid, return None.
        o If not, return a string explaining why.
        """
        if not password:
            return _(u'You must enter a password.')

        if len(password) < 5 and not _checkPermission(ManagePortal, self):
            return _(u'Your password must contain at least 5 characters.')

        if confirm is not None and confirm != password:
            return _(u'Your password and confirmation did not match. '
                     u'Please try again.')

        return None

    security.declarePublic( 'testPropertiesValidity' )
    def testPropertiesValidity(self, props, member=None):

        """ Verify that the properties supplied satisfy portal's requirements.

        o If the properties are valid, return None.
        o If not, return a string explaining why.
        """
        if member is None: # New member.

            username = props.get('username', '')
            if not username:
                return _(u'You must enter a valid name.')

            if not self.isMemberIdAllowed(username):
                return _(u'The login name you selected is already in use or '
                         u'is not valid. Please choose another.')

            email = props.get('email')
            if email is None:
                return _(u'You must enter an email address.')

            try:
                checkEmailAddress(email)
            except ValidationError:
                return _(u'You must enter a valid email address.')

        else: # Existing member.
            email = props.get('email')

            if email is not None:
                try:
                    checkEmailAddress(email)
                except ValidationError:
                    return _(u'You must enter a valid email address.')

            # Not allowed to clear an existing non-empty email.
            existing = member.getProperty('email')

            if existing and email == '':
                return _(u'You must enter a valid email address.')

        return None

    security.declarePublic( 'mailPassword' )
    def mailPassword(self, forgotten_userid, REQUEST):
        """ Email a forgotten password to a member.

        o Raise an exception if user ID is not found.
        """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool
        membership = getToolByName(self, 'portal_membership')
        member = membership.getMemberById(forgotten_userid)

        if member is None:
            raise ValueError(_(u'The username you entered could not be '
                               u'found.'))

        email = self._getValidEmailAddress(member)

        # Rather than have the template try to use the mailhost, we will
        # render the message ourselves and send it from here (where we
        # don't need to worry about 'UseMailHost' permissions).
        method = self.password_email
        kw = {'member': member, 'password': member.getPassword()}

        if getattr(aq_base(method), 'isDocTemp', 0):
            mail_text = method(self, REQUEST, **kw)
        else:
            mail_text = method(**kw)

        host = getUtility(IMailHost)
        host.send( mail_text )

        return self.mail_password_response( self, REQUEST )

    security.declarePublic( 'registeredNotify' )
    def registeredNotify(self, new_member_id, password=None, REQUEST=None):
        """ Handle mailing the registration / welcome message.
        """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool and uses self.REQUEST
        if REQUEST is None:
            REQUEST = self.REQUEST
            warn("registeredNotify should be called with 'REQUEST' as third "
                 "argument. The BBB code will be removed in CMF 2.3.",
                 DeprecationWarning, stacklevel=2)

        membership = getToolByName( self, 'portal_membership' )
        member = membership.getMemberById( new_member_id )

        if member is None:
            raise ValueError(_(u'The username you entered could not be '
                               u'found.'))

        if password is None:
            password = member.getPassword()

        email = self._getValidEmailAddress(member)

        # Rather than have the template try to use the mailhost, we will
        # render the message ourselves and send it from here (where we
        # don't need to worry about 'UseMailHost' permissions).
        method = self.registered_email
        kw = {'member': member, 'password': password, 'email': email}

        if getattr(aq_base(method), 'isDocTemp', 0):
            mail_text = method(self, REQUEST, **kw)
        else:
            mail_text = method(**kw)

        host = getUtility(IMailHost)
        host.send( mail_text )

    security.declareProtected(ManagePortal, 'editMember')
    @postonly
    def editMember(self, member_id, properties=None, password=None,
                   roles=None, domains=None, REQUEST=None):
        """ Edit a user's properties and security settings

        o Checks should be done before this method is called using
          testPropertiesValidity and testPasswordValidity
        """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool
        mtool = getToolByName(self, 'portal_membership')
        member = mtool.getMemberById(member_id)
        member.setMemberProperties(properties)
        member.setSecurityProfile(password,roles,domains)

        return member

InitializeClass(RegistrationTool)
