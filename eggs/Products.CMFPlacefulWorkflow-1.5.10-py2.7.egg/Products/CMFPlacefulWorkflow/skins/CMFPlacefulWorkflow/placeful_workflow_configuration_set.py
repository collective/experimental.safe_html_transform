##parameters=policy_in='', policy_below='', update_security=False
##title=set placeful workflow configuration
##
from Products.CMFCore.utils import getToolByName
from Products.CMFPlacefulWorkflow import CMFPlacefulWorkflowMessageFactory as _

request = context.REQUEST

# Form submission will either have update_security as a key
# meaning user wants to do it OR no key at all. If this script
# is called directly, we use the parameter
update_security = ('update_security' in request.form) or update_security

# This script is used for both the save and cancel button
cancel = False
submit = request.form.get('submit', None)
if submit is not None and submit == 'Cancel':
    cancel = True
    message = _(u'Configuration changes cancelled.')

if not cancel:
    tool = getToolByName(context, 'portal_placeful_workflow')
    config = tool.getWorkflowPolicyConfig(context)
    if not config:
        message = _(u'No config in this folder.')
    else:
        if not tool.isValidPolicyName(policy_in) and not policy_in == '':
            raise AttributeError("%s is not a valid policy id" % policy_in)

        if not tool.isValidPolicyName(policy_below) and not policy_below == '':
            raise AttributeError("%s is not a valid policy id" % policy_below)

        config.setPolicyIn(policy_in, update_security)
        config.setPolicyBelow(policy_below, update_security)

        message = _('Changed policies.')

context.plone_utils.addPortalMessage(message)
request.RESPONSE.redirect('placeful_workflow_configuration')
