from zope.formlib.interfaces import IFormFields
from zope.interface import Attribute


class IFormFieldsets(IFormFields):
    """A grouped collection of form fields (IFormField objects).
    """

    id = Attribute("An id for the fieldset")

    label = Attribute("The label used for the fieldset")

    description = Attribute("An optional description used for the fieldset")

    fieldsets = Attribute("The fieldset definitions")

    def __add__(form_fields):
        """Add two form fieldsets (IFormFieldsets) or add additional fields to
        an existing fieldset.

        Return a new IFormFieldsets which is a nested representation of the two.
        
        In order to fullfill the IFormFields API we make all fields available
        from the base IFormFieldsets.
        """
