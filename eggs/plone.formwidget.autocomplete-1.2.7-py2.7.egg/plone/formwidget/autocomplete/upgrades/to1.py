from Products.CMFCore.utils import getToolByName

def install_formwidget_autocomplete(context):
    """Re-import jsregistry items to pick up new javscript file"""
    gs = getToolByName(context, 'portal_setup')
    profile = 'profile-plone.formwidget.autocomplete:default'
    gs.runImportStepFromProfile(profile, 'jsregistry', purge_old=False)
