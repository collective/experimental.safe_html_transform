import zope.interface
from plone.rfc822.interfaces import IMessageAPI

zope.interface.moduleProvides(IMessageAPI)

from plone.rfc822._utils import constructMessageFromSchema
from plone.rfc822._utils import constructMessageFromSchemata
from plone.rfc822._utils import constructMessage

from plone.rfc822._utils import renderMessage

from plone.rfc822._utils import initializeObjectFromSchema
from plone.rfc822._utils import initializeObjectFromSchemata
from plone.rfc822._utils import initializeObject
