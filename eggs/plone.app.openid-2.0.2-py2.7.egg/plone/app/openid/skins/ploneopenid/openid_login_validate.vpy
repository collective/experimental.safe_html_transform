## Script (Python) "openid_login_validate"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=openid_url=""
##title=Validate OpenID login attempt
##

from plone.app.openid import PloneMessageFactory as _

if not openid_url:
    context.plone_utils.addPortalMessage(_(u'Please enter your identity URL.'), 'warning')
    state.setError('openid_url',
        _(u'Please enter your identity URL.'), 'openid_url_required')

return state

