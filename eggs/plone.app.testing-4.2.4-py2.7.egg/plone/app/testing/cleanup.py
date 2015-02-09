"""Cleanup handlers for various global registries
"""

from zope.testing.cleanup import addCleanUp

# Make sure cleanup handlers from GenericSetup are registered
try:
    import Products.GenericSetup.zcml
except ImportError:
    pass

# Make sure cleanup handlers from PAS are registered
try:
    import Products.PluggableAuthService.zcml
except ImportError:
    pass


def cleanUpMultiPlugins():
    try:
        from Products.PluggableAuthService.PluggableAuthService import MultiPlugins
    except ImportError:
        pass
    else:

        zap = []

        # Don't stomp on the things the other cleanup handler will deal with
        from Products.PluggableAuthService import zcml
        for plugin in MultiPlugins:
            if plugin not in zcml._mt_regs:
                zap.append(plugin)

        for plugin in zap:
            MultiPlugins.remove(plugin)

addCleanUp(cleanUpMultiPlugins)
del addCleanUp
