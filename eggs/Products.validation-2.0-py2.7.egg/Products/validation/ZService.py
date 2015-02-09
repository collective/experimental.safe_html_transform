from Products.validation.service import Service

from Acquisition import Implicit
from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo

from AccessControl import ModuleSecurityInfo

# make validator service public
security = ModuleSecurityInfo('Products.validation.config')
security.declarePublic('validation')

class ZService(Service, Implicit):
    """Service running in a zope site - exposes some methods""" 

    security = ClassSecurityInfo()

    security.declarePublic('validate')
    security.declarePublic('__call__')
    security.declarePublic('validatorFor')

InitializeClass(ZService) 
