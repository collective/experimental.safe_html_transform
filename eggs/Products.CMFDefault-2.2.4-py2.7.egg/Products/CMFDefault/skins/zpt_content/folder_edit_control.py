##parameters=title, description, **kw
##
from Products.CMFDefault.utils import Message as _

if title!=context.Title() or description != context.Description():
    context.edit(title=title, description=description)
    return context.setStatus(True, _(u'Metadata changed.'))
else:
    return context.setStatus(False, _(u'Nothing to change.'))
