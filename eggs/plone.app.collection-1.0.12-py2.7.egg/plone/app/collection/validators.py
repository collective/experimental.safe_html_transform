from Products.validation.interfaces.IValidator import IValidator
from zope.interface import implements


class NonJavascriptValidator:
    """
        This validator is added when accessing the new style collections
        without javascript.
        The validation error is needed to stay in in the current form,
        which keeps archetypes from creating a temp object in
        portal_factory keeps archetypes from losing the request/parser info
    """
    implements(IValidator)

    name = 'nonjavascriptvalidator'

    def __init__(self, name, title='', description=''):
        self.name = name

    def __call__(self, value, instance, *args, **kwargs):
        """Call the validator"""
        # value  is only empty when not using javascript
        if len(value) == 0:
            return u"Please finish your search terms / criteria"
        return 1


validatorList = [
    NonJavascriptValidator('javascriptDisabled', title='', description=''),
    ]

__all__ = ('validatorList', )
