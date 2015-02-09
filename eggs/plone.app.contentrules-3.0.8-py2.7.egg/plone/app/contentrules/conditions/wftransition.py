from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from zope.component import adapts
from zope.formlib import form
from zope.interface import implements, Interface
from zope import schema

from OFS.SimpleItem import SimpleItem
from Products.CMFCore.interfaces import IActionSucceededEvent

from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.formhelper import AddForm, EditForm


class IWorkflowTransitionCondition(Interface):
    """Interface for the configurable aspects of a workflow transition condition.

    This is also used to create add and edit forms, below.
    """

    wf_transitions = schema.Set(title=_(u"Workflow transition"),
                           description=_(u"The workflow transitions to check for."),
                           required=True,
                           value_type=schema.Choice(vocabulary="plone.app.vocabularies.WorkflowTransitions"))


class WorkflowTransitionCondition(SimpleItem):
    """The actual persistent implementation of the workflow transition condition element.
    """
    implements(IWorkflowTransitionCondition, IRuleElementData)

    wf_transitions = []
    element = "plone.conditions.WorkflowTransition"

    @property
    def summary(self):
        return _(u"Workflow transitions are: ${transitions}", mapping=dict(transitions=", ".join(self.wf_transitions)))


class WorkflowTransitionConditionExecutor(object):
    """The executor for this condition.
    """
    implements(IExecutable)
    adapts(Interface, IWorkflowTransitionCondition, IActionSucceededEvent)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        return self.event.action in self.element.wf_transitions


class WorkflowTransitionAddForm(AddForm):
    """An add form for workflow transition conditions.
    """
    form_fields = form.FormFields(IWorkflowTransitionCondition)
    label = _(u"Add Workflow Transition Condition")
    description = _(u"A workflow transition condition can restrict rules to "
        "execute only after a certain transition.")
    form_name = _(u"Configure element")

    def create(self, data):
        c = WorkflowTransitionCondition()
        form.applyChanges(c, self.form_fields, data)
        return c


class WorkflowTransitionEditForm(EditForm):
    """An edit form for portal type conditions

    Formlib does all the magic here.
    """
    form_fields = form.FormFields(IWorkflowTransitionCondition)
    label = _(u"Edit Workflow Transition Condition")
    description = _(u"A workflow transition condition can restrict rules to "
        "execute only after a certain transition.")
    form_name = _(u"Configure element")
