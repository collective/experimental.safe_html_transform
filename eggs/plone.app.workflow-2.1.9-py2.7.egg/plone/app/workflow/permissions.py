from Products.CMFCore.permissions import setDefaultRoles
from AccessControl import ModuleSecurityInfo

security = ModuleSecurityInfo("plone.app.workflow.permissions")

# Controls access to the "sharing" page
security.declarePublic("DelegateRoles")
DelegateRoles = "Sharing page: Delegate roles"
setDefaultRoles(DelegateRoles, ('Manager', 'Site Administrator', 'Owner', 'Editor', 'Reviewer', ))

# Control the individual roles
security.declarePublic("DelegateReaderRole")
DelegateReaderRole = "Sharing page: Delegate Reader role"
setDefaultRoles(DelegateReaderRole, ('Manager', 'Site Administrator', 'Owner', 'Editor', 'Reviewer'))

security.declarePublic("DelegateEditorRole")
DelegateEditorRole = "Sharing page: Delegate Editor role"
setDefaultRoles(DelegateEditorRole, ('Manager', 'Site Administrator', 'Owner', 'Editor'))

security.declarePublic("DelegateContributorRole")
DelegateContributorRole = "Sharing page: Delegate Contributor role"
setDefaultRoles(DelegateContributorRole, ('Manager', 'Site Administrator', 'Owner',))

security.declarePublic("DelegateReviewerRole")
DelegateReviewerRole = "Sharing page: Delegate Reviewer role"
setDefaultRoles(DelegateReviewerRole, ('Manager', 'Site Administrator', 'Reviewer',))
