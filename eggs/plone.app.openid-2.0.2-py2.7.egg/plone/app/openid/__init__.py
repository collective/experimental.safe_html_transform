from zope.i18nmessageid import MessageFactory
PloneMessageFactory = MessageFactory('plone')

from AccessControl import ModuleSecurityInfo
ModuleSecurityInfo('plone.app.openid').declarePublic('PloneMessageFactory')
