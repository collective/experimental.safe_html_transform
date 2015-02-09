from zope.interface import implements
from Products.validation.i18n import PloneMessageFactory as _
from Products.validation.i18n import recursiveTranslate
from Products.validation.i18n import safe_unicode
from Products.validation.interfaces.IValidator import IValidator

_marker = []


class EmptyValidator:
    implements(IValidator)

    def __init__(self, name, title='', description='', showError=True):
        self.name = name
        self.title = title or name
        self.description = description
        self.showError = showError

    def __call__(self, value, *args, **kwargs):
        isEmpty  = kwargs.get('isEmpty', False)
        instance = kwargs.get('instance', None)
        field    = kwargs.get('field', None)

        # XXX: This is a temporary fix. Need to be fixed right for AT 2.0
        #      content_edit / BaseObject.processForm() calls
        #      widget.process_form a second time!
        if instance and field:
            widget  = field.widget
            request = getattr(instance, 'REQUEST', None)
            if request and request.form:
                form   = request.form
                result = widget.process_form(instance, field, form,
                                             empty_marker=_marker,
                                             emptyReturnsMarker=True)
                if result is _marker or result is None:
                    isEmpty = True

        if isEmpty:
            return True
        elif value == '' or value is None:
            return True
        else:
            if getattr(self, 'showError', False):
                msg =  _(u"Validation failed($name): '$value' is not empty.",
                         mapping = { 'name' : safe_unicode(self.name), 'value': safe_unicode(value)})
                return recursiveTranslate(msg, **kwargs)
            else:
                return False

validatorList = [
    EmptyValidator('isEmpty', title='', description=''),
    EmptyValidator('isEmptyNoError', title='', description='', showError=False),
    ]

__all__ = ('validatorList', )

