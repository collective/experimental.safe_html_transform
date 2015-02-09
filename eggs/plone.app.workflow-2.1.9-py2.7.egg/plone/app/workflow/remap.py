import transaction

SAVE_THRESHOLD = 100 # Do a savepoint every so often
_marker = object()

from Products.CMFCore.utils import getToolByName
from Products.DCWorkflow.utils import modifyRolesForPermission
#from Persistence import PersistentMapping
#from Acquisition import aq_base
from DateTime import DateTime


def remap_workflow(context, type_ids, chain, state_map={}):
    """Change the workflow for each type in type_ids to use the workflow
    chain given. state_map is a dictionary of old state names to
    new ones. States that are not found will be remapped to the default
    state of the new workflow.
    """

    if chain is None:
        chain = '(Default)'

    portal_workflow = getToolByName(context, 'portal_workflow')

    default_chain = portal_workflow.getDefaultChain()
    chains_by_type = dict(portal_workflow.listChainOverrides())

    # Build a dictionary of type id -> chain before we made changes
    old_chains = dict([(t, chains_by_type.get(t, default_chain)) for t in type_ids])

    # Work out which permissions were managed by the old chain, but not
    # by the new chain. This may vary by type id.

    # Update the workflow chain in portal_workflows.

    # XXX: There is no decent API for this it seems :-(
    if chain == '(Default)':
        cbt = portal_workflow._chains_by_type
        for type_id in type_ids:
            if type_id in cbt:
                del cbt[type_id]
    else:
        portal_workflow.setChainForPortalTypes(type_ids, chain)

    # Now remap, and fix permissions

    # For each portal type, work out which workflows were controlling them
    # before, and which permissions were in that, which are not in the new
    # chain. These permissions need to be reset to 'Acquire'.

    chain_workflows = {}
    new_chain_permissions = set()
    permissions_to_reset = {}

    if chain == '(Default)':
        chain = default_chain
    for c in chain:
        if c not in chain_workflows:
            chain_workflows[c] = getattr(portal_workflow, c)
            for permission in chain_workflows[c].permissions:
                new_chain_permissions.add(permission)

    for typeid, oc in old_chains.items():
        if oc == '(Default)':
            oc = default_chain
        permissions_to_reset[typeid] = set()
        for c in oc:
            if c not in chain_workflows:
                chain_workflows[c] = getattr(portal_workflow, c)
            for permission in chain_workflows[c].permissions:
                if permission not in new_chain_permissions:
                    permissions_to_reset[typeid].add(permission)

    portal_catalog = getToolByName(context, 'portal_catalog')

    # Then update the state of each
    remapped_count = 0
    threshold_count = 0
    for brain in portal_catalog(portal_type=type_ids):
        obj = brain.getObject()
        portal_type = brain.portal_type

        # If there are permissions to reset to acquire, do so now
        for permission in permissions_to_reset[brain.portal_type]:
            # A list makes it acquire ... if it was a tuple, it wouldn't
            modifyRolesForPermission(obj, permission, [])

        # Work out what, if any, the previous state of the object was

        if len(chain) > 0:
            old_chain = old_chains[portal_type]
            old_wf = None
            if len(old_chain) > 0:
                old_wf = chain_workflows[old_chain[0]]

            old_state = None
            if old_wf is not None:
                old_status = portal_workflow.getStatusOf(old_wf.getId(), obj)
                if old_status is not None:
                    old_state = old_status.get('review_state', None)

            # Now add a transition
            for new_wf_name in chain:
                new_wf = chain_workflows[new_wf_name]
                new_status = {'action': None,
                              'actor': None,
                              'comments': 'State remapped from control panel',
                              'review_state': state_map.get(old_state, new_wf.initial_state),
                              'time': DateTime()}
                portal_workflow.setStatusOf(new_wf_name, obj, new_status)

                # Trigger any automatic transitions, or else just make sure the role mappings are right
                auto_transition = new_wf._findAutomaticTransition(obj, new_wf._getWorkflowStateOf(obj))
                if auto_transition is not None:
                    new_wf._changeStateOf(obj, auto_transition)
                else:
                    new_wf.updateRoleMappingsFor(obj)

        obj.reindexObject(idxs=['allowedRolesAndUsers', 'review_state'])

        remapped_count += 1
        threshold_count += 1

        if threshold_count > SAVE_THRESHOLD:
            transaction.savepoint()
            threshold_count = 0

    return remapped_count
