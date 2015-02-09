##parameters=delete=None, add=None
##title=set local workflow policies prefs
##

from Products.CMFPlacefulWorkflow import CMFPlacefulWorkflowMessageFactory as _
from Products.CMFCore.utils import getToolByName

request = context.REQUEST

policy_ids = request.get('policy_ids',[])
policy_id = request.get('policy_id', None)
policy_duplicate_id = request.get('policy_duplicate_id', 'empty')

pwtool = getToolByName(context, 'portal_placeful_workflow')
plone_utils = getToolByName(context, 'plone_utils')

if delete and policy_ids:
    for policy_id in policy_ids:
        if policy_id in pwtool.objectIds():
            pwtool.manage_delObjects([policy_id,])
    plone_utils.addPortalMessage(_(u'Deleted Local Workflow Policy.'), 'info')
    request.RESPONSE.redirect('prefs_workflow_localpolicies_form')

elif add:
    if policy_id:
        pwtool.manage_addWorkflowPolicy(id=policy_id, duplicate_id=policy_duplicate_id)
        plone_utils.addPortalMessage(_(u'Local Workflow Policy added.'), 'info')
        request.RESPONSE.redirect('prefs_workflow_policy_mapping?wfpid='+policy_id)

    else:
        plone_utils.addPortalMessage(_(u'The policy Id is required.'), 'error')
        request.RESPONSE.redirect('prefs_workflow_localpolicies_form')
