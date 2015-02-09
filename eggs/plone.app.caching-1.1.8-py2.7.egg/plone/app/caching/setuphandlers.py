from Products.CMFCore.utils import getToolByName

def enableExplicitMode():
    """ZCML startup hook to put the ruleset registry into explict mode.
    This means we require people to declare ruleset types before using them.
    """
    from z3c.caching.registry import getGlobalRulesetRegistry
    registry = getGlobalRulesetRegistry()
    if registry is not None:
        registry.explicit = True

def importVarious(context):

    if not context.readDataFile('plone.app.caching.txt'):
        return

    site = context.getSite()

    error_log = getToolByName(site, 'error_log')

    properties = error_log.getProperties()
    ignored = properties.get('ignored_exceptions', ())

    modified = False
    for exceptionName in ('Intercepted',):
        if exceptionName not in ignored:
            ignored += (exceptionName,)
            modified = True

    if modified:
        error_log.setProperties(properties.get('keep_entries', 10),
                                properties.get('copy_to_zlog', True),
                                ignored)
