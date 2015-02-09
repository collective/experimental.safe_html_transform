##parameters=**kw
##title=Paste objects to a folder from the clipboard
##
from Products.CMFDefault.exceptions import CopyError
from Products.CMFDefault.exceptions import zExceptions_Unauthorized
from Products.CMFDefault.utils import Message as _

try:
    result = context.manage_pasteObjects(context.REQUEST['__cp'])
    if len(result) == 1:
        return context.setStatus(True, _(u'Item pasted.'))
    else:
        return context.setStatus(True, _(u'Items pasted.'))
except CopyError:
    return context.setStatus(False, _(u'CopyError: Paste failed.'))
except zExceptions_Unauthorized:
    return context.setStatus(False, _(u'Unauthorized: Paste failed.'))
