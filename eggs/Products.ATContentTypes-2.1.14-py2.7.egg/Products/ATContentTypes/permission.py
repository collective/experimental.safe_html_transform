from Products.CMFCore.permissions import setDefaultRoles
from Products.Archetypes.atapi import listTypes
from Products.ATContentTypes.config import PROJECTNAME
from Products.ATContentTypes.interfaces import IATTopic
from Products.ATContentTypes.interfaces import IATTopicCriterion

TYPE_ROLES = ('Manager', 'Site Administrator', 'Owner')
TOPIC_ROLES = ('Manager', 'Site Administrator')
CHANGE_TOPIC_ROLES = TOPIC_ROLES + ('Owner',)
CRITERION_ROLES = ('Manager', 'Site Administrator')

# Gathering Topic and Event related permissions into one place
AddTopics = 'Add portal topics'
setDefaultRoles(AddTopics, TOPIC_ROLES)

ChangeTopics = 'Change portal topics'
setDefaultRoles(ChangeTopics, CHANGE_TOPIC_ROLES)

ChangeEvents = 'Change portal events'
setDefaultRoles(ChangeEvents, ('Manager', 'Site Administrator', 'Owner',))

ModifyConstrainTypes = "Modify constrain types"
setDefaultRoles(ModifyConstrainTypes, ('Manager', 'Site Administrator', 'Owner'))

ModifyViewTemplate = "Modify view template"
setDefaultRoles(ModifyViewTemplate, ('Manager', 'Site Administrator', 'Owner'))

ViewHistory = "ATContentTypes: View history"
setDefaultRoles(ViewHistory, ('Manager', 'Site Administrator'))

UploadViaURL = "ATContentTypes: Upload via url"
setDefaultRoles(UploadViaURL, ('Manager', 'Site Administrator'))

permissions = {}


def wireAddPermissions():
    """Creates a list of add permissions for all types in this project

    Must be called **after** all types are registered!
    """
    global permissions
    atct_types = listTypes(PROJECTNAME)
    for atct in atct_types:
        if IATTopic.implementedBy(atct['klass']):
            permission = AddTopics
        elif IATTopicCriterion.implementedBy(atct['klass']):
            permission = "%s Topic: Add %s" % (PROJECTNAME, atct['portal_type'])
            setDefaultRoles(permission, CRITERION_ROLES)
        else:
            permission = "%s: Add %s" % (PROJECTNAME, atct['portal_type'])
            setDefaultRoles(permission, TYPE_ROLES)

        permissions[atct['portal_type']] = permission
    return permissions
