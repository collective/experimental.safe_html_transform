from z3c.form import validator
from zope.schema import ValidationError

from plone.namedfile.interfaces import INamedField
from plone.formwidget.namedfile import MessageFactory as _

class InvalidState(ValidationError):
    __doc__ = _(u'No file provided.')

class NamedFileWidgetValidator(validator.SimpleFieldValidator):
    
    def validate(self, value, force=False):
        """See interfaces.IValidator"""
        action = self.request.get("%s.action" % self.widget.name, None)
        if action == 'replace' and value is None:
            raise InvalidState()
        return super(NamedFileWidgetValidator, self).validate(value, force)

validator.WidgetValidatorDiscriminators(NamedFileWidgetValidator, field=INamedField)
