from Acquisition import aq_parent
from Acquisition import aq_inner
from Acquisition import aq_base
from Acquisition import aq_get
from zExceptions import BadRequest
from OFS import ObjectManager
from Products.validation.interfaces.IValidator import IValidator
from zope.interface import implements
from Products.validation.i18n import PloneMessageFactory as _
from Products.validation.i18n import recursiveTranslate
from Products.validation.i18n import safe_unicode


class IdValidator:
    implements(IValidator)

    def __init__( self, name, title='', description=''):
        self.name = name
        self.title = title or name
        self.description = description

    def __call__(self, id, instance, *args, **kwargs):
        try:
            # try to use the check_id script of CMFPlone
            check_id = aq_get(instance, 'check_id', None, 1)
            if check_id is None:
                raise AttributeError('check_id script not found')
            return check_id(id, required=kwargs.get('required', 0)) or 1
        except AttributeError:
            # space test
            if ' ' in id:
                msg =  _(u'Spaces are not allowed in ids')
                return recursiveTranslate(msg, **kwargs)

            # in parent test
            parent = aq_parent(aq_inner(instance))
            # If the id is given to a different object already
            if id in parent.objectIds() and getattr(aq_base(parent), id) is not aq_base(instance):
                msg = _(u'Id $id is already in use',
                        mapping = {'id': safe_unicode(id)})
                return recursiveTranslate(msg, **kwargs)

            # objet manager test
            # XXX: This is f***ed
            try:
                ObjectManager.checkValidId(self, id, allow_dup=1)
            except BadRequest, m:
                return str(m)
            return 1

validatorList = [
    IdValidator('isValidId', title='', description=''),
    ]

__all__ = ('validatorList', )
