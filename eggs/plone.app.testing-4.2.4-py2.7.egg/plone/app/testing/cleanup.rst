Cleanup functions
-----------------

When imported, this package will register a few cleanup handlers with
``zope.testing.cleanup`` to clean up global state left by various Zope, CMF
and Plone packages.

    >>> import zope.testing.cleanup
    >>> zope.testing.cleanup.cleanUp()

PluggableAuthService MultiPlugins list
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``PluggableAuthService`` package maintains a global list of so-called
multi-plugins.

    >>> from Products.PluggableAuthService import PluggableAuthService
    >>> PluggableAuthService.MultiPlugins
    []

A new plugin can be registered using the ``registerPlugin()`` API.

    >>> PluggableAuthService.registerMultiPlugin("dummy_plugin")
    >>> PluggableAuthService.MultiPlugins
    ['dummy_plugin']

On cleanup, this list is emptied.

    >>> zope.testing.cleanup.cleanUp()

    >>> PluggableAuthService.MultiPlugins
    []
