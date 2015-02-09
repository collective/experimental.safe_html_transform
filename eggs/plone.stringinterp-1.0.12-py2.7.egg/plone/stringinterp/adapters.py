#!/usr/bin/env python
# encoding: utf-8
"""
adapters.py

Created by Steve McMahon on 2009-08-12.
Copyright (c) 2009 Plone Foundation.
"""

from zope.interface import implements, Interface
from zope.component import adapts
from zope.i18n import translate
from zope.site.hooks import getSite

from AccessControl import Unauthorized
from Acquisition import aq_inner, aq_parent, aq_get

from Products.PlonePAS.interfaces.group import IGroupData
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import (
    IContentish, IMinimalDublinCore, IWorkflowAware, IDublinCore,
    ICatalogableDublinCore)
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.utils import safe_unicode
from Products.CMFPlone.i18nl10n import ulocalized_time

from plone.memoize.request import memoize_diy_request

from plone.stringinterp import _
from plone.stringinterp.interfaces import IStringSubstitution


class BaseSubstitution(object):
    implements(IStringSubstitution)

    def __init__(self, context):
        self.context = context

    # __call__ is a wrapper for the subclassed
    # adapter's actual substitution that makes sure we're
    # not generating unauth exceptions or returning non-unicode.
    def __call__(self):
        try:
            return safe_unicode(self.safe_call())
        except Unauthorized:
            return _(u'Unauthorized')


class UrlSubstitution(BaseSubstitution):
    adapts(IContentish)

    category = _(u'All Content')
    description = _(u'URL')

    def safe_call(self):
        return self.context.absolute_url()


class ParentIdSubstitution(BaseSubstitution):
    adapts(Interface)

    category = _(u'All Content')
    description = _(u"Identifier of the parent content or login of managed user")

    def safe_call(self):
        return aq_parent(self.context).getId()


class IdSubstitution(BaseSubstitution):
    adapts(Interface)

    category = _(u'All Content')
    description = _(u"Identifier of the content or login of managed user")

    def safe_call(self):
        return self.context.getId()


class ParentUrlSubstitution(BaseSubstitution):
    adapts(IContentish)

    category = _(u'All Content')
    description = _(u"Folder URL")

    def safe_call(self):
        return aq_get(aq_parent(self.context), 'absolute_url')()


class TitleSubstitution(BaseSubstitution):
    adapts(IMinimalDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Title')

    def safe_call(self):
        return self.context.Title()


class ParentTitleSubstitution(BaseSubstitution):
    adapts(IContentish)

    category = _(u'All Content')
    description = _(u'Parent title')

    def safe_call(self):
        return aq_get(aq_parent(self.context), 'Title')()


class DescriptionSubstitution(BaseSubstitution):
    adapts(IMinimalDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Description')

    def safe_call(self):
        return self.context.Description()


class TypeSubstitution(BaseSubstitution):
    adapts(IMinimalDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Content Type')

    def safe_call(self):
        return translate(self.context.Type(), context=self.context.REQUEST)

class CreatorSubstitution(BaseSubstitution):
    adapts(IDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Creator Id')

    def safe_call(self):
        for creator in self.context.listCreators():
            return creator
        return ''

class CreatorFullNameSubstitution(CreatorSubstitution):
    adapts(IContentish)

    category = _(u'Dublin Core')
    description = _(u'Creator Full Name')

    def safe_call(self):
        creator = super(CreatorFullNameSubstitution, self).safe_call()
        if not creator:
            return ''

        pm = getToolByName(self.context, "portal_membership")
        member = pm.getMemberById(creator)
        if not member:
            return creator

        fname = member.getProperty('fullname', None)
        if not fname:
            return creator
        return fname

class CreatorEmailSubstitution(CreatorSubstitution):
    adapts(IDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Creator E-Mail')

    def safe_call(self):
        creator = super(CreatorEmailSubstitution, self).safe_call()
        if not creator:
            return ''
        pm = getToolByName(self.context, "portal_membership")
        member = pm.getMemberById(creator)
        if not member:
            return ''
        email = member.getProperty('email', '')
        if not email:
            return ''
        return email

class CreatorsSubstitution(BaseSubstitution):
    adapts(IDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Creators Ids')

    def safe_call(self):
        return  ', '.join(self.context.listCreators())

class CreatorsEmailsSubstitution(BaseSubstitution):
    adapts(IDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Creators E-Mails')

    def safe_call(self):
        creators = self.context.listCreators()
        pm = getToolByName(self.context, "portal_membership")
        emails = []
        for creator in creators:
            member = pm.getMemberById(creator)
            if not member:
                continue
            email = member.getProperty('email', None)
            if not email:
                continue
            emails.append(email)
        return ', '.join(emails)

class ContributorsSubstitution(BaseSubstitution):
    adapts(IDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Contributors Ids')

    def safe_call(self):
        return  ', '.join(self.context.listContributors())

class ContributorsEmailsSubstitution(BaseSubstitution):
    adapts(IDublinCore)

    category = (u'Dublin Core')
    description = _(u'Contributors E-Mails')

    def safe_call(self):
        contributors = self.context.listContributors()
        pm = getToolByName(self.context, "portal_membership")
        emails = []
        for contributor in contributors:
            member = pm.getMemberById(contributor)
            if not member:
                continue
            email = member.getProperty('email', None)
            if not email:
                continue
            emails.append(email)
        return ', '.join(emails)

class SubjectSubstitution(BaseSubstitution):
    adapts(IDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Subject')

    def safe_call(self):
        return  ', '.join(self.context.Subject())


class FormatSubstitution(BaseSubstitution):
    adapts(IDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Format')

    def safe_call(self):
        return  self.context.Format()


class LanguageSubstitution(BaseSubstitution):
    adapts(IDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Language')

    def safe_call(self):
        return  self.context.Language()


class IdentifierSubstitution(BaseSubstitution):
    adapts(IDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Identifier, actually URL of the content')

    def safe_call(self):
        return  self.context.Identifier()


class RightsSubstitution(BaseSubstitution):
    adapts(IDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Rights')

    def safe_call(self):
        return  self.context.Rights()


class ReviewStateSubstitution(BaseSubstitution):
    adapts(IWorkflowAware)

    category = _(u'Workflow')
    description = _(u'Review State')

    def safe_call(self):
        wft = getToolByName(self.context, 'portal_workflow')
        return wft.getInfoFor(self.context, 'review_state')


class ReviewStateTitleSubstitution(BaseSubstitution):
    adapts(IWorkflowAware)

    category = _(u'Workflow')
    description = _(u'Review State Title')

    def safe_call(self):
        wft = getToolByName(self.context, 'portal_workflow')
        review_state = wft.getInfoFor(self.context, 'review_state')
        return _(wft.getTitleForStateOnType(review_state,
                                            self.context.portal_type))


class DateSubstitution(BaseSubstitution):

    def formatDate(self, adate):
        try:
            return safe_unicode(
               ulocalized_time(adate, long_format=True, context=self.context))
        except ValueError:
            return u'???'


class CreatedSubstitution(DateSubstitution):
    adapts(ICatalogableDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Date Created')

    def safe_call(self):
        return self.formatDate(self.context.created())


class EffectiveSubstitution(DateSubstitution):
    adapts(ICatalogableDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Date Effective')

    def safe_call(self):
        return self.formatDate(self.context.effective())


class ExpiresSubstitution(DateSubstitution):
    adapts(ICatalogableDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Date Expires')

    def safe_call(self):
        return self.formatDate(self.context.expires())


class ModifiedSubstitution(DateSubstitution):
    adapts(ICatalogableDublinCore)

    category = _(u'Dublin Core')
    description = _(u'Date Modified')

    def safe_call(self):
        return self.formatDate(self.context.modified())


# A base class for adapters that need member information
class MemberSubstitution(BaseSubstitution):
    adapts(IContentish)

    def __init__(self, context):
        self.context = context
        self.mtool = getToolByName(self.context, "portal_membership")
        self.gtool = getToolByName(self.context, "portal_groups")

    def getMembersFromIds(self, ids):
        members = set()
        for id in ids:
            member = self.mtool.getMemberById(id)
            if member is not None:
                members.add(member)
            else:
                # id may be for a group
                group = self.gtool.getGroupById(id)
                if group is not None:
                    members = members.union(group.getGroupMembers())
        return members

    def getPropsForMembers(self, members, propname):
        pset = set()
        for member in members:
            prop = member.getProperty(propname, None)
            if prop:
                pset.add(prop)
        return pset

    def getPropsForIds(self, ids, propname):
        return self.getPropsForMembers(self.getMembersFromIds(ids), propname)


# A base class for all the role->email list adapters
class MailAddressSubstitution(MemberSubstitution):
    adapts(IContentish)

    def getEmailsForRole(self, role):

        portal = getSite()
        acl_users = getToolByName(portal, 'acl_users')

        # get a set of ids of members with the global role
        ids = set([p[0] for p in acl_users.portal_role_manager.listAssignedPrincipals(role)])

        # union with set of ids of members with the local role
        ids |= set([id for id, irole
                       in acl_users._getAllLocalRoles(self.context).items()
                       if role in irole])

        # get members from group or member ids
        members = _recursiveGetMembersFromIds(portal, ids)

        # get emails
        return u', '.join(self.getPropsForMembers(members, 'email'))


def _recursiveGetMembersFromIds(portal, group_and_user_ids):
    """ get members from a list of group and member ids """

    gtool = getToolByName(portal, 'portal_groups')
    mtool = getToolByName(portal, 'portal_membership')
    members = set()

    def recursiveGetGroupUsers(mtool, gtool, group):
        users = set()
        if IGroupData.providedBy(group):
            group_members = group.getGroupMembers()
        else:
            group_members = [mtool.getMemberById(m) for m in group.getMemberIds()]

        for group_or_user in group_members:
            if IGroupData.providedBy(group_or_user):
                users = users.union(
                            recursiveGetGroupUsers(mtool, gtool, group_or_user))
            elif group_or_user is not None:
                # Other group data PAS plugins might not filter no
                # longer existing group members.
                users.add(group_or_user)

        return users

    for group_or_user_id in group_and_user_ids:
        _group = gtool.getGroupById(group_or_user_id)
        if _group:
            members = members.union(recursiveGetGroupUsers(mtool, gtool, _group))
        else:
            member = mtool.getMemberById(group_or_user_id)
            if member is not None:
                members.add(member)

    return members


class OwnerEmailSubstitution(MailAddressSubstitution):

    category = _(u'Local Roles')
    description = _(u'Owners E-Mails')

    def safe_call(self):
        return self.getEmailsForRole('Owner')


class ReviewerEmailSubstitution(MailAddressSubstitution):

    category = _(u'Local Roles')
    description = _(u'Reviewers E-Mails')

    def safe_call(self):
        return self.getEmailsForRole('Reviewer')


class ReaderEmailSubstitution(MailAddressSubstitution):

    category = _(u'Local Roles')
    description = _(u'Readers E-Nails')

    def safe_call(self):
        return self.getEmailsForRole('Reader')


class ContributorEmailSubstitution(MailAddressSubstitution):

    category = _(u'Local Roles')
    description = _(u'Contributors E-Mails')

    def safe_call(self):
        return self.getEmailsForRole('Contributor')


class EditorEmailSubstitution(MailAddressSubstitution):

    category = _(u'Local Roles')
    description = _(u'Editors E-Mails')

    def safe_call(self):
        return self.getEmailsForRole('Editor')


class ManagerEmailSubstitution(MailAddressSubstitution):

    category = _(u'Local Roles')
    description = _(u'Managers E-Mails')

    def safe_call(self):
        return self.getEmailsForRole('Manager')


class MemberEmailSubstitution(MailAddressSubstitution):

    category = _(u'Local Roles')
    description = _(u'Members E-Mails')

    def safe_call(self):
        return self.getEmailsForRole('Member')


class UserEmailSubstitution(BaseSubstitution):
    adapts(IContentish)

    category = _(u'Current User')
    description = _(u'E-Mail Address')

    def safe_call(self):
        pm = getToolByName(self.context, "portal_membership")
        if not pm.isAnonymousUser():
            user = pm.getAuthenticatedMember()
            if user is not None:
                email = user.getProperty('email', None)
                if email:
                    return email
        return u''


class UserFullNameSubstitution(BaseSubstitution):
    adapts(IContentish)

    category = _(u'Current User')
    description = _(u'Full Name')

    def safe_call(self):
        pm = getToolByName(self.context, "portal_membership")
        if not pm.isAnonymousUser():
            user = pm.getAuthenticatedMember()
            if user is not None:
                fname = user.getProperty('fullname', None)
                if fname:
                    return fname
                else:
                    return user.getId()

        return u''


class UserIdSubstitution(BaseSubstitution):
    adapts(IContentish)

    category = _(u'Current User')
    description = _(u'Id')

    def safe_call(self):
        pm = getToolByName(self.context, "portal_membership")
        if not pm.isAnonymousUser():
            user = pm.getAuthenticatedMember()
            if user is not None:
                return user.getId()
        return u''


# memoize on the request an expensive function called by the
# ChangeSubstitution class.
@memoize_diy_request()
def _lastChange(request, context):
    workflow_change = _lastWorkflowChange(context)
    last_revision = _lastRevision(context)
    if not workflow_change:
        return last_revision
    elif not last_revision:
        return workflow_change

    if workflow_change and last_revision and \
       workflow_change.get('time') > last_revision.get('time'):
        return workflow_change

    return last_revision


def _lastWorkflowChange(context):
    workflow = getToolByName(context, 'portal_workflow')
    try:
        review_history = workflow.getInfoFor(context, 'review_history')
    except WorkflowException:
        return {}

    # filter out automatic transitions.
    review_history = [r for r in review_history if r['action']]

    if review_history:
        r = review_history[-1]
        r['type'] = 'workflow'
        r['transition_title'] = \
            workflow.getTitleForTransitionOnType(
             r['action'],
             context.portal_type)
        r['actorid'] = r['actor']
    else:
        r = {}

    return r


def _lastRevision(context):
    context = aq_inner(context)
    rt = getToolByName(context, "portal_repository")
    if rt.isVersionable(context):
        history = rt.getHistoryMetadata(context)
        if history:
            # history = ImplicitAcquisitionWrapper(history, pa)
            meta = history.retrieve(
               history.getLength(countPurged=False)-1,
               countPurged=False,
              )['metadata']['sys_metadata']
            return dict(type='versioning',
                    action=_(u"edit"),
                    transition_title=_(u"Edit"),
                    actorid=meta["principal"],
                    time=meta["timestamp"],
                    comments=meta['comment'],
                    review_state=meta["review_state"],
                    )

    return {}


# a base class for substitutions that use
# last revision or workflow information
class ChangeSubstitution(BaseSubstitution):

    def lastChangeMetadata(self, id):
        return  _lastChange(self.context.REQUEST, self.context).get(id, '')


class LastChangeCommentSubstitution(ChangeSubstitution):
    adapts(IContentish)

    category = _(u'History')
    description = _(u'Comment')

    def safe_call(self):
        return self.lastChangeMetadata('comments')


class LastChangeTitleSubstitution(ChangeSubstitution):
    adapts(IContentish)

    category = _(u'History')
    description = _(u'Transition title')

    def safe_call(self):
        return self.lastChangeMetadata('transition_title')


class LastChangeTypeSubstitution(ChangeSubstitution):
    adapts(IContentish)

    category = _(u'History')
    description = _(u'Change type')

    def safe_call(self):
        return self.lastChangeMetadata('type')


class LastChangeActorIdSubstitution(ChangeSubstitution):
    adapts(IContentish)

    category = _(u'History')
    description = _(u'Change author')

    def safe_call(self):
        return self.lastChangeMetadata('actorid')


class PortalSubstitution(BaseSubstitution):

    category = _(u'Portal')

    def __init__(self, context):
        BaseSubstitution.__init__(self, context)
        self.portal = getToolByName(context, 'portal_url').getPortalObject()

class PortalURLSubstitution(PortalSubstitution):

    description = _(u'Portal URL')

    def safe_call(self):
        return self.portal.absolute_url()


class PortalTitleSubstitution(PortalSubstitution):

    description = _(u'Portal title')

    def safe_call(self):
        return self.portal.Title()
