from zope.interface import Interface
from zope import schema

from z3c.form.interfaces import IFields, IGroup, IGroupForm

class IFormExtender(Interface):
    """A component that can add, modify, sort and group fields in a form.

    This should be a named multi adapter from (context, request, form).
    """

    order = schema.Int(title=u"Order",
                       description=u"Use this property to order the sorter. " +
                                   u"Low numbers are executed before high ones.",
                       required=True)

    def update():
        """Modify the form in place. Supported operations include:

         - modify the 'fields' object to change the default fieldset
         - modify the 'groups' list to add, remove or reorder fieldsets
         - modify the 'fields' property of a given group
        """

class IDescriptiveGroup(IGroup):
    """Extension to z3c.form's Group class that can separate out a name,
    a label and a description.
    """

    __name__ = schema.TextLine(title=u"Name of this group")

    label = schema.TextLine(title=u"Fieldset title",
                            description=u"The __name__ will be used if this is not given",
                            required=False)

    description = schema.Text(title=u"Fieldset description",
                              required=False)

class IGroupFactory(Interface):
    """An object that can be used to create a z3c.form.group.Group.
    """

    __name__ = schema.TextLine(title=u"Name of this group")

    label = schema.TextLine(title=u"Fieldset title",
                            description=u"The __name__ will be used if this is not given",
                            required=False)

    description = schema.Text(title=u"Fieldset description",
                              required=False)

    fields = schema.Object(title=u"Fields in this form", schema=IFields)

class IExtensibleForm(Interface):
    """A special version of the IGroupForm that is extensible via
    IFormExtender adapters.
    """

    groups = schema.List(title=u'Groups',
                         value_type=schema.Object(title=u"Group", schema=IGroupFactory))

    default_fieldset_label = schema.TextLine(title=u"Label of the default fieldset")

    def updateFields():
        """Called during form update to allow updating of self.fields
        and self.groups.
        """
