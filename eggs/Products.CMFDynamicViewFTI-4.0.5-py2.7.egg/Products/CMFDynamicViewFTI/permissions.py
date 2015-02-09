from Products.CMFCore.permissions import setDefaultRoles

ModifyViewTemplate = "Modify view template"
setDefaultRoles(ModifyViewTemplate, ('Manager', 'Owner'))
