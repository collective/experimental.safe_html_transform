
We just import the storage.

    >>> from plone.app.viewletmanager.storage import ViewletSettingsStorage
    >>> storage = ViewletSettingsStorage()

By default there is no order stored in the storage.

    >>> storage.getOrder('plone.top', 'Plone Default')
    ()

There are also no viewlets which should be hidden stored in the storage.

    >>> storage.getHidden('plone.top', 'Plone Default')
    ()

We can now store the order by names of viewlets in the storage.

    >>> storage.setOrder('plone.top', 'Plone Default',
    ...                    ('plone.logo', 'plone.global_tabs'))

And it will be returned.

    >>> storage.getOrder('plone.top', 'Plone Default')
    ('plone.logo', 'plone.global_tabs')

The default skin should now be that same one for that manager.

    >>> storage.getDefault('plone.top')
    'Plone Default'

For other skins it would then return the default order.

    >>> storage.getOrder('plone.top', 'Undefined')
    ('plone.logo', 'plone.global_tabs')

We can still set another default order if needed.

    >>> storage.setOrder('plone.top', 'MySkin',
    ...                    ('plone.global_tabs', 'plone.logo'))
    >>> storage.setDefault('plone.top', 'MySkin')
    >>> storage.getOrder('plone.top', 'Undefined')
    ('plone.global_tabs', 'plone.logo')

The first skin should still render as before.

    >>> storage.getOrder('plone.top', 'Plone Default')
    ('plone.logo', 'plone.global_tabs')

For other viewletmanagers it should still return nothing.

    >>> storage.getOrder('plone.bottom', 'Plone Default')
    ()

The storage is a utility, so test if it works like that.

    >>> import zope.component
    >>> from plone.app.viewletmanager.interfaces import IViewletSettingsStorage

    >>> zope.component.getUtility(IViewletSettingsStorage)
    Traceback (most recent call last):
        ...
    ComponentLookupError: (<InterfaceClass plone.app.viewletmanager.interfaces.IViewletSettingsStorage>, '')

    >>> zope.component.provideUtility(storage, IViewletSettingsStorage)

    >>> zope.component.getUtility(IViewletSettingsStorage)
    <plone.app.viewletmanager.storage.ViewletSettingsStorage object at ...>
