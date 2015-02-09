##parameters=**kw
##
from Products.CMFCore.utils import getUtilityByInterfaceName
from Products.CMFDefault.utils import Message as _

ptool = getUtilityByInterfaceName('Products.CMFCore.interfaces.IPropertiesTool')

if not ptool.hasProperty('enable_actionicons'):
    ptool.manage_addProperty('enable_actionicons', '', 'boolean')

kw.setdefault('enable_actionicons', False)

ptool.editProperties(kw)

return context.setStatus(True, _(u'CMF Settings changed.'))
