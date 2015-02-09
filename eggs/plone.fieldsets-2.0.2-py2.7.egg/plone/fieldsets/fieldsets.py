from zope.schema import getFieldsInOrder
from zope.formlib.form import FormField
from zope.formlib.form import FormFields
from zope.formlib.form import _initkw
from zope.interface import implements
from zope.interface.interface import InterfaceClass
from zope.schema.interfaces import IField

from interfaces import IFormFieldsets

class FormFieldsets(FormFields):
    """
    Let's make sure that this implementation actually fulfills the API.

      >>> from zope.interface.verify import verifyClass
      >>> verifyClass(IFormFieldsets, FormFieldsets)
      True
      """

    implements(IFormFieldsets)

    id = ''
    label = None
    description = None
    fieldsets = ()

    def __init__(self, *args, **kw):
        # Most of this code is copied from zope.formlib.form.Formfields
        # licensed under the ZPL 2.1
        keep_readonly, omit_readonly, defaults = _initkw(**kw)

        fields = []
        fieldsets = ()
        for arg in args:
            if isinstance(arg, InterfaceClass):
                for name, field in getFieldsInOrder(arg):
                    fields.append((name, field))
            elif IField.providedBy(arg):
                name = arg.__name__
                if not name:
                    raise ValueError("Field has no name")
                fields.append((name, arg))
            elif isinstance(arg, FormFieldsets):
                fieldsets = fieldsets + (arg, )
                for form_field in arg:
                    fields.append((form_field.__name__, form_field))
            elif isinstance(arg, FormFields):
                for form_field in arg:
                    fields.append((form_field.__name__, form_field))
            elif isinstance(arg, FormField):
                fields.append((arg.__name__, arg))
            else:
                raise TypeError("Unrecognized argument type", arg)

        self.fieldsets = fieldsets

        seq = []
        byname = {}
        for name, field in fields:
            if isinstance(field, FormField):
                form_field = field
            else:
                if field.readonly:
                    if omit_readonly and (name not in keep_readonly):
                        continue
                form_field = FormField(field, **defaults)
                name = form_field.__name__

            if name in byname:
                raise ValueError("Duplicate name", name)
            seq.append(form_field)
            byname[name] = form_field

        self.__FormFields_seq__ = seq
        self.__FormFields_byname__ = byname

    def __add__(self, other):
        if not isinstance(other, FormFieldsets) and \
           not isinstance(other, FormFields):
            return NotImplemented
        return self.__class__(self, other)
