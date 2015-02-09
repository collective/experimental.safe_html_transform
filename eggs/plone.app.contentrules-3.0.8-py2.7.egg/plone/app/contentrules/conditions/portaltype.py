from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from zope.component import adapts
from zope.interface import implements, Interface
from zope.formlib import form
from zope import schema
from zope.site.hooks import getSite
from zope.i18n import translate

from Acquisition import aq_inner, aq_base
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import ITypesTool

from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import AddForm, EditForm


class IPortalTypeCondition(Interface):
    """Interface for the configurable aspects of a portal type condition.

    This is also used to create add and edit forms, below.
    """

    check_types = schema.Set(title=_(u"Content type"),
                              description=_(u"The content type to check for."),
                              required=True,
                              value_type=schema.Choice(vocabulary="plone.app.vocabularies.ReallyUserFriendlyTypes"))


class PortalTypeCondition(SimpleItem):
    """The actual persistent implementation of the portal type condition element.

    Note that we must mix in SimpleItem to keep Zope 2 security happy.
    """
    implements(IPortalTypeCondition, IRuleElementData)

    check_types = []
    element = "plone.conditions.PortalType"

    @property
    def summary(self):
        portal = getSite()
        portal_types = getToolByName(portal, 'portal_types')
        titles = []
        for name in self.check_types:
            fti = getattr(portal_types, name, None)
            if fti is not None:
                title = translate(fti.Title(), context=portal.REQUEST)
                titles.append(title)
        return _(u"Content types are: ${names}", mapping=dict(names=", ".join(titles)))


class PortalTypeConditionExecutor(object):
    """The executor for this condition.

    This is registered as an adapter in configure.zcml
    """
    implements(IExecutable)
    adapts(Interface, IPortalTypeCondition, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        obj = aq_inner(self.event.object)
        if not hasattr(aq_base(obj), 'getTypeInfo'):
            return False
        elif ITypesTool.providedBy(obj):
            # types tool have a getTypeInfo method
            return False

        ti = obj.getTypeInfo() # getTypeInfo can be None
        if ti is None:
            return False
        return ti.getId() in self.element.check_types


class PortalTypeAddForm(AddForm):
    """An add form for portal type conditions.
    """
    form_fields = form.FormFields(IPortalTypeCondition)
    label = _(u"Add Content Type Condition")
    description = _(u"A portal type condition makes the rule apply only to certain content types.")
    form_name = _(u"Configure element")

    def create(self, data):
        c = PortalTypeCondition()
        form.applyChanges(c, self.form_fields, data)
        return c


class PortalTypeEditForm(EditForm):
    """An edit form for portal type conditions
    """
    form_fields = form.FormFields(IPortalTypeCondition)
    label = _(u"Edit Content Type Condition")
    description = _(u"A portal type condition makes the rule apply only to certain content types.")
    form_name = _(u"Configure element")
