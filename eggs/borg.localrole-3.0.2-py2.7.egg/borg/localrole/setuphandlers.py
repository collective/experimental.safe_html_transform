from borg.localrole.utils import setup_localrole_plugin

def importVarious(context):

    if context.readDataFile('borg.localrole_various.txt') is None:
        return

    portal = context.getSite()
    setup_localrole_plugin(portal)
