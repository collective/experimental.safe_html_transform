## Script (Python) "validatePassword"
##parameters=password='', confirm='', **kw
##title=
##
from Products.CMFCore.utils import getUtilityByInterfaceName
from Products.CMFCore.utils import getToolByName

ptool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IPropertiesTool')
rtool = getToolByName(script, 'portal_registration')

if ptool.getProperty('validate_email'):
    password = rtool.generatePassword()
    return context.setStatus(True, password=password)
else:
    result = rtool.testPasswordValidity(password, confirm)
    if result:
        return context.setStatus(False, result)
    else:
        return context.setStatus(True)
