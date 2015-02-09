##parameters=
##title=add workflow policy configuration
##

from Products.CMFPlacefulWorkflow import CMFPlacefulWorkflowMessageFactory as _

context.manage_addProduct['CMFPlacefulWorkflow'].manage_addWorkflowPolicyConfig()

context.plone_utils.addPortalMessage(_(u'Workflow policy configuration added.'))
context.REQUEST.RESPONSE.redirect('placeful_workflow_configuration')
