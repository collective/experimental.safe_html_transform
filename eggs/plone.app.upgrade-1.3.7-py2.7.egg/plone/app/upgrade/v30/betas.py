from StringIO import StringIO

from zope.component import queryUtility

from Products.CMFActionIcons.interfaces import IActionIconsTool
from Products.CMFCore.Expression import Expression
from Products.CMFCore.interfaces import IActionProvider
from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile


def beta1_beta2(context):
    """ 3.0-beta1 -> 3.0-beta2
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v30:3.0b1-3.0b2')


def beta2_beta3(context):
    """ 3.0-beta2 -> 3.0-beta3
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v30:3.0b2-3.0b3')


def beta3_rc1(context):
    """ 3.0-beta3 -> 3.0-rc1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v30:3.0b3-3.0b4')


def migrateHistoryTab(context):
    portal_actions = getToolByName(context, 'portal_actions', None)
    if portal_actions is not None:
        objects = getattr(portal_actions, 'object', None)
        if objects is not None:
            if 'rss' in objects.objectIds():
                objects.manage_renameObjects(['rss'], ['history'])
                logger.info('Upgraded history action.')


def changeOrderOfActionProviders(context):
    portal_actions = getToolByName(context, 'portal_actions', None)
    if portal_actions is not None:
        portal_actions.deleteActionProvider('portal_actions')
        portal_actions.addActionProvider('portal_actions')
        logger.info('Changed the order of action providers.')

def cleanupOldActions(context):
    portal_actions = getToolByName(context, 'portal_actions', None)
    if portal_actions is not None:
        # Remove some known unused actions from the object_tabs category and
        # remove the category completely if no actions are left
        object_tabs = getattr(portal_actions, 'object_tabs', None)
        if object_tabs is not None:
            if 'contentrules' in object_tabs.objectIds():
                object_tabs._delObject('contentrules')
            if 'change_ownership' in object_tabs.objectIds():
                object_tabs._delObject('change_ownership')
            if len(object_tabs.objectIds()) == 0:
                del object_tabs
                portal_actions._delObject('object_tabs')
                logger.info('Removed object_tabs action category.')
        object_ = getattr(portal_actions, 'object', None)
        if object_ is not None:
            if 'reply' in object_.objectIds():
                object_._delObject('reply')
        user = getattr(portal_actions, 'user', None)
        if user is not None:
            if 'logged_in' in user.objectIds():
                user._delObject('logged_in')
            if 'myworkspace' in user.objectIds():
                user._delObject('myworkspace')
        global_ = getattr(portal_actions, 'global', None)
        if global_ is not None:
            if 'manage_members' in global_.objectIds():
                global_._delObject('manage_members')
            if 'configPortal' in global_.objectIds():
                global_._delObject('configPortal')
            if len(global_.objectIds()) == 0:
                del global_
                portal_actions._delObject('global')
                logger.info('Removed global action category.')

def cleanDefaultCharset(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    charset = portal.getProperty('default_charset', None)
    if charset is not None:
        if not charset.strip():
            portal.manage_delProperties(['default_charset'])
            logger.info('Removed empty default_charset portal property')


def addAutoGroupToPAS(context):
    from Products.PlonePAS.Extensions.Install import activatePluginInterfaces

    portal = getToolByName(context, 'portal_url').getPortalObject()
    sout = StringIO()

    if not portal.acl_users.objectIds(['Automatic Group Plugin']):
        from Products.PlonePAS.plugins.autogroup import manage_addAutoGroup
        manage_addAutoGroup(portal.acl_users, 'auto_group',
                'Automatic Group Provider',
                'AuthenticatedUsers', "Logged-in users (Virtual Group)")
        activatePluginInterfaces(portal, "auto_group", sout)
        logger.info("Added automatic group PAS plugin")

def removeS5Actions(context):
    portalTypes = getToolByName(context, 'portal_types', None)
    if portalTypes is not None:
        document = portalTypes.restrictedTraverse('Document', None)
        if document:
            ids = [x.getId() for x in document.listActions()]
            if 's5_presentation' in ids:
                index = ids.index('s5_presentation')
                document.deleteActions([index])
                logger.info("Removed 's5_presentation' action from actions tool.")

    iconsTool = queryUtility(IActionIconsTool)
    if iconsTool is not None:
        ids = [x._action_id for x in iconsTool.listActionIcons()]
        if 's5_presentation' in ids:
            iconsTool.removeActionIcon('plone','s5_presentation')
            logger.info("Removed 's5_presentation' icon from actionicons tool.")

def addContributorToCreationPermissions(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    if 'Contributor' not in portal.valid_roles():
        portal._addRole('Contributor')
    if 'Contributor' not in portal.acl_users.portal_role_manager.listRoleIds():
        portal.acl_users.portal_role_manager.addRole('Contributor')

    for p in ['Add portal content', 'Add portal folders', 'ATContentTypes: Add Document',
                'ATContentTypes: Add Event',
                'ATContentTypes: Add File', 'ATContentTypes: Add Folder',
                'ATContentTypes: Add Image', 'ATContentTypes: Add Link',
                'ATContentTypes: Add News Item', ]:
        roles = [r['name'] for r in portal.rolesOfPermission(p) if r['selected']]
        if 'Contributor' not in roles:
            roles.append('Contributor')
            portal.manage_permission(p, roles, bool(portal.acquiredRolesAreUsedBy(p)))

def removeSharingAction(context):
    portal_types = getToolByName(context, 'portal_types', None)
    if portal_types is not None:
        for fti in portal_types.objectValues():
            action_ids = [a.id for a in fti.listActions()]
            if 'local_roles' in action_ids:
                fti.deleteActions([action_ids.index('local_roles')])

        logger.info('Removed explicit references to sharing action')

def addEditorToSecondaryEditorPermissions(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    for p in ['Manage properties', 'Modify view template', 'Request review']:
        roles = [r['name'] for r in portal.rolesOfPermission(p) if r['selected']]
        if 'Editor' not in roles:
            roles.append('Editor')
            portal.manage_permission(p, roles, bool(portal.acquiredRolesAreUsedBy(p)))

def updateEditActionConditionForLocking(context):
    """
    Condition on edit views for Document, Event, File, Folder, Image,
    Link, Topic has been added to not display the Edit
    tab if an item is locked
    """
    portal_types = getToolByName(context, 'portal_types', None)
    lockable_types = ['Document', 'Event', 'File', 'Folder',
                      'Image', 'Link', 'News Item', 'Topic']
    if portal_types is not None:
        for contentType in lockable_types:
            fti = portal_types.getTypeInfo(contentType)
            if fti:
                for action in fti.listActions():
                    if action.getId() == 'edit' and not action.condition:
                        action.condition = Expression("not:object/@@plone_lock_info/is_locked_for_current_user|python:True")

def addOnFormUnloadJS(context):
    """
    add the form unload JS to the js registry
    """
    jsreg = getToolByName(context, 'portal_javascripts', None)
    script = 'unlockOnFormUnload.js'
    if jsreg is not None:
        script_ids = jsreg.getResourceIds()
        # Failsafe: first make sure the stylesheet doesn't exist in the list
        if script not in script_ids:
            jsreg.registerScript(script,
                                 enabled = True,
                                 cookable = True)
            # put it at the bottom of the stack
            jsreg.moveResourceToBottom(script)
            logger.info("Added " + script + " to portal_javascripts")

def updateTopicTitle(context):
    """Update the title of the topic type."""
    tt = getToolByName(context, 'portal_types', None)
    if tt is not None:
        topic = tt.get('Topic')
        if topic is not None:
            topic.title = 'Collection'


def cleanupActionProviders(context):
    """Remove no longer existing action proiders."""
    at = getToolByName(context, "portal_actions")
    for provider in at.listActionProviders():
        candidate = getToolByName(context, provider, None)
        if candidate is None or not IActionProvider.providedBy(candidate):
            at.deleteActionProvider(provider)
            logger.info("%s is no longer an action provider" % provider)

def hidePropertiesAction(context):
    tt = getToolByName(context, 'portal_types', None)
    if not IActionProvider.providedBy(tt):
        return
    for ti in tt.listTypeInfo():
        actions = ti.listActions()
        index=[i for i in range(len(actions) )
                if actions[i].category=="object" and
                   actions[i].id=="metadata"]
        if index:
            ti.deleteActions(index)
            logger.info("Removed properties action from type %s" % ti.id)
