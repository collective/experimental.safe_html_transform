from zope.interface import implements
from zope.component import getAdapters

from plone.z3cform.fieldsets.interfaces import IExtensibleForm
from plone.z3cform.fieldsets.interfaces import IFormExtender

from z3c.form.group import GroupForm

from plone.z3cform.fieldsets import utils

from plone.z3cform import MessageFactory as _

def order_key(adapter_tuple):
    return adapter_tuple[1].order

class FormExtender(object):
    """Base class for IFormExtender adapters with convenience APIs
    """
    implements(IFormExtender)

    # Change this to prioritise
    order = 0

    def __init__(self, context, request, form):
        self.context = context
        self.request = request
        self.form = form

    def add(self, *args, **kwargs):
        """Add one or more fields. Keyword argument 'index' can be used to
        specify an index to insert at. Keyword argument 'group' can be used
        to specify the label of a group, which will be found and used or
        created if it doesn't exist.
        """

        utils.add(self.form, *args, **kwargs)

    def remove(self, field_name, prefix=None):
        """Get rid of a field. The omitted field will be returned.
        """

        return utils.remove(self.form, field_name, prefix=prefix)

    def move(self, field_name, before=None, after=None, prefix=None, relative_prefix=None):
        """Move the field with the given name before or after another field.
        """

        utils.move(self.form, field_name, before=before, after=after,
                    prefix=prefix, relative_prefix=relative_prefix)

class ExtensibleForm(GroupForm):
    implements(IExtensibleForm)

    groups = []
    default_fieldset_label = _(u"Default")

    def update(self):
        self.updateFields()
        super(ExtensibleForm, self).update()

    def updateFields(self):
        extenders = getAdapters((self.context, self.request, self), IFormExtender)
        for name, extender in sorted(extenders, key=order_key):
            extender.update()
