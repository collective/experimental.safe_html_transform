from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from zope.component import adapts
from zope.interface import implements, Interface
from zope.formlib import form
from zope import schema

from Acquisition import aq_inner
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName

from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import AddForm, EditForm


class IRoleCondition(Interface):
    """Interface for the configurable aspects of a role condition.

    This is also used to create add and edit forms, below.
    """

    role_names = schema.Set(title=_(u"Roles"),
                            description=_(u"The roles to check for."),
                            required=True,
                            value_type=schema.Choice(vocabulary="plone.app.vocabularies.Roles"))


class RoleCondition(SimpleItem):
    """The actual persistent implementation of the role condition element.

    Note that we must mix in SimpleItem to keep Zope 2 security happy.
    """
    implements(IRoleCondition, IRuleElementData)

    role_names = []
    element = "plone.conditions.Role"

    @property
    def summary(self):
        return _(u"Roles are: ${names}", mapping=dict(names=", ".join(self.role_names)))


class RoleConditionExecutor(object):
    """The executor for this condition.

    This is registered as an adapter in configure.zcml
    """
    implements(IExecutable)
    adapts(Interface, IRoleCondition, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        portal_membership = getToolByName(self.context, 'portal_membership', None)
        if portal_membership is None:
            return False
        member = portal_membership.getAuthenticatedMember()
        roles_in_context = member.getRolesInContext(aq_inner(self.event.object))
        for r in self.element.role_names:
            if r in roles_in_context:
                return True
        return False


class RoleAddForm(AddForm):
    """An add form for role rule conditions.
    """
    form_fields = form.FormFields(IRoleCondition)
    label = _(u"Add Role Condition")
    description = _(u"A role condition can prevent rules from executing unless "
        "the current user has a particular role.")
    form_name = _(u"Configure element")

    def create(self, data):
        c = RoleCondition()
        form.applyChanges(c, self.form_fields, data)
        return c


class RoleEditForm(EditForm):
    """An edit form for role conditions
    """
    form_fields = form.FormFields(IRoleCondition)
    label = _(u"Add Role Condition")
    description = _(u"A role condition can prevent rules from executing unless "
        "the current user has a particular role.")
    form_name = _(u"Configure element")
