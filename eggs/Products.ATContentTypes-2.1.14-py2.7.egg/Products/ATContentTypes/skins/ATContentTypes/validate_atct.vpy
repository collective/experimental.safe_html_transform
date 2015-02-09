## Script (Python) "validate_atct"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##

errors  = {}
request = context.REQUEST
form    = request.form
from Products.ATContentTypes import ATCTMessageFactory as _

## It's hacky and not nice but it's working
# Set the title from the filename of uploaded image or field
# The title has to be set before the validation. This is the only place to do it
# right although it's looking hackish.
pfield = context.getPrimaryField()
if pfield:
    pfname = pfield.getName()
    title = form.get('title', context.Title())
    file = form.get('%s_file' % pfname, None)

    if not title and file:
        if file:
            filename = getattr(file, 'filename', None)

        if filename:
            form['title'] = filename.split('\\')[-1]
## eoXXX

errors  = context.validate(REQUEST=request, errors=errors, data=1, metadata=0)

if errors:
    msg = _(u'Please correct the indicated errors.')
    context.plone_utils.addPortalMessage(msg, 'error')
    return state.set(status='failure', errors=errors)

msg = _(u'Changes saved.')
context.plone_utils.addPortalMessage(msg)
return state
