from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from zope.component import adapts
from zope.interface import implements, Interface
from zope.formlib import form
from zope import schema

from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import getToolByName

from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import AddForm, EditForm

from Products.CMFCore.Expression import Expression, createExprContext


class ITalesExpressionCondition(Interface):
    """Interface for the configurable aspects of a TALES expression condition.

    This is also used to create add and edit forms, below.
    """

    tales_expression = schema.TextLine(title=_(u"TALES expression"),
                              description=_(u"The TALES expression to check."),
                              required=True,
                              )


class TalesExpressionCondition(SimpleItem):
    """The actual persistent implementation of the TALES expression condition element.
    """
    implements(ITalesExpressionCondition, IRuleElementData)

    tales_expression = ''
    element = "plone.conditions.TalesExpression"

    @property
    def summary(self):
        return _(u"TALES expression is: ${tales_expression}",
                 mapping={'tales_expression': self.tales_expression})


class TalesExpressionConditionExecutor(object):
    """The executor for this condition.

    This is registered as an adapter in configure.zcml
    """
    implements(IExecutable)
    adapts(Interface, ITalesExpressionCondition, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        object = self.event.object
        folder = self.context
        portal = getToolByName(folder, 'portal_url').getPortalObject()
        expression = self.element.tales_expression
        ec = createExprContext(folder, portal, object)
        # Workaround CMFCore/PageTemplates issue with unicode missing context
        ec.contexts['context'] = ec.contexts['here']
        return bool(Expression(expression)(ec))


class TalesExpressionAddForm(AddForm):
    """An add form for tales expression condition.
    """
    form_fields = form.FormFields(ITalesExpressionCondition)
    label = _(u"Add TALES Expression Condition")
    description = _(u"A TALES expression condition makes the rule apply "
                     "only if TALES expression is not False in context.")
    form_name = _(u"Configure element")

    def create(self, data):
        c = TalesExpressionCondition()
        form.applyChanges(c, self.form_fields, data)
        return c


class TalesExpressionEditForm(EditForm):
    """An edit form for TALES expression condition
    """
    form_fields = form.FormFields(ITalesExpressionCondition)
    label = _(u"Edit TALES Expression Condition")
    description = _(u"A TALES expression condition makes the rule apply "
                     "only if TALES expression is not False in context.")
    form_name = _(u"Configure element")
