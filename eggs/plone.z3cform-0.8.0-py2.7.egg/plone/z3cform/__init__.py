import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory('plone.z3cform')

from plone.z3cform.patch import apply_patch
apply_patch()
