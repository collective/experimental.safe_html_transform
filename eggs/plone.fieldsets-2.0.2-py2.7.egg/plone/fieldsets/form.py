from plone.fieldsets.interfaces import IFormFieldsets
from zope.formlib import form

from five.formlib.formbase import FormBase, EditForm


class FieldsetsEditForm(EditForm):
    """An edit form which supports fieldsets."""

    def setUpWidgets(self, ignore_request=False):
        # First part is copied from zope.formlib.form.EditForm licensed under
        # the ZPL 2.1
        self.adapters = {}
        # In order to support fieldsets, we need to setup the widgets on all
        # the fieldsets as well.
        if self.is_fieldsets():
            self.widgets = None
            for fieldset in self.form_fields.fieldsets:
                fieldset.widgets = form.setUpEditWidgets(
                    fieldset, self.prefix, self.context, self.request,
                    adapters=self.adapters, ignore_request=ignore_request
                    )
                if self.widgets is None:
                    self.widgets = fieldset.widgets
                else:
                    self.widgets += fieldset.widgets
        else:
            self.widgets = form.setUpEditWidgets(
                self.form_fields, self.prefix, self.context, self.request,
                adapters=self.adapters, ignore_request=ignore_request
                )

    def is_fieldsets(self):
        # We need to be able to test for non-fieldsets in templates.
        return IFormFieldsets.providedBy(self.form_fields)


class FieldsetsInputForm(FormBase):
    """An input form which supports fieldsets."""

    def setUpWidgets(self, ignore_request=False):
        # In order to support fieldsets, we need to setup the widgets on all
        # the fieldsets as well.
        if self.is_fieldsets():
            self.widgets = None
            for fieldset in self.form_fields.fieldsets:
                fieldset.widgets = form.setUpInputWidgets(
                    fieldset, self.prefix, self.context, self.request,
                    ignore_request=ignore_request
                    )
                if self.widgets is None:
                    self.widgets = fieldset.widgets
                else:
                    self.widgets += fieldset.widgets
        else:
            self.widgets = form.setUpInputWidgets(
                self.form_fields, self.prefix, self.context, self.request,
                ignore_request=ignore_request
                )

    def is_fieldsets(self):
        # We need to be able to test for non-fieldsets in templates.
        return IFormFieldsets.providedBy(self.form_fields)
