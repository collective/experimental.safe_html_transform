from Products.validation.config import validation
from zope.i18nmessageid import MessageFactory

from plone.app.collection.validators import NonJavascriptValidator

PloneMessageFactory = MessageFactory('plone')


def initialize(context):
    from plone.app.collection import config
    from Products.Archetypes import atapi
    from Products.CMFCore import utils

    content_types, constructors, ftis = atapi.process_types(
        atapi.listTypes(config.PROJECTNAME),
        config.PROJECTNAME)

    for atype, constructor in zip(content_types, constructors):
        utils.ContentInit('%s: %s' % (config.PROJECTNAME, atype.portal_type),
            content_types=(atype, ),
            permission=config.ADD_PERMISSIONS[atype.portal_type],
            extra_constructors=(constructor, ),
            ).initialize(context)

validation.register(NonJavascriptValidator('javascriptDisabled'))

__all__ = ('PloneMessageFactory', )
