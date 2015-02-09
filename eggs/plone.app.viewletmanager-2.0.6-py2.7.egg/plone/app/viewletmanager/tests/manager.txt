
We need a storage for the viewlet settings.

    >>> from zope.component import provideUtility, provideAdapter, getAdapters
    >>> from zope.interface import implements, Interface
    >>> from plone.app.viewletmanager.storage import ViewletSettingsStorage
    >>> from plone.app.viewletmanager.interfaces import IViewletSettingsStorage

    >>> storage = ViewletSettingsStorage()
    >>> provideUtility(storage,
    ...                IViewletSettingsStorage)

We also need a fake request.

    >>> from zope.publisher.browser import TestRequest
    >>> request = TestRequest()

We need some fake content. It needs a getCurrentSkinName to fake the function
in Plone.

    >>> # yeah, yeah, we still need acquisition here and an Application
    >>> from Acquisition import Explicit
    >>> class Content(Explicit):
    ...     implements(Interface)
    ...
    ...     def getCurrentSkinName(self):
    ...         return getattr(self, 'skin', 'Plone Default')
    >>> content = Content()

Now we need a view on the content.

    >>> from zope.publisher.interfaces.browser import IBrowserView
    >>> from Products.Five.browser import BrowserView as View
    >>> view = View(content, request)

Now we need a manager.

    >>> from zope.viewlet.interfaces import IViewletManager
    >>> class ILeftColumn(IViewletManager):
    ...     """Viewlet manager located in the left column."""

We need to use our custom manager base.

    >>> from Products.Five.viewlet.manager import ViewletManager
    >>> from plone.app.viewletmanager.manager import OrderedViewletManager
    >>> LeftColumn = ViewletManager('left', ILeftColumn,
    ...                             bases=(OrderedViewletManager,))

Now we can instantiate the manager.

    >>> manager = LeftColumn(content, request, view)

Initially there are no viewlets in it.

    >>> manager.update()
    >>> manager.render()
    u''

Now we need some dummy viewlets.

    >>> from zope.viewlet.interfaces import IViewlet
    >>> from zope.publisher.interfaces.browser import IDefaultBrowserLayer
    >>> class BaseViewlet(Explicit):
    ...     implements(IViewlet)
    ...
    ...     __allow_access_to_unprotected_subobjects__ = 1
    ...
    ...     def __init__(self, context, request, view, manager):
    ...         self.__parent__ = view
    ...         self.context = context
    ...         self.request = request
    ...
    ...     def update(self):
    ...         pass
    ...
    ...     def render(self):
    ...         return self.name

    >>> class FirstViewlet(BaseViewlet):
    ...     name = u"first"

    >>> provideAdapter(
    ...     FirstViewlet,
    ...     (Interface, IDefaultBrowserLayer,
    ...      IBrowserView, ILeftColumn),
    ...     IViewlet, name='first')

    >>> class SecondViewlet(BaseViewlet):
    ...     name = u"second"

    >>> provideAdapter(
    ...     SecondViewlet,
    ...     (Interface, IDefaultBrowserLayer,
    ...      IBrowserView, ILeftColumn),
    ...     IViewlet, name='second')

    >>> class ThirdViewlet(BaseViewlet):
    ...     name = u"third"

    >>> provideAdapter(
    ...     ThirdViewlet,
    ...     (Interface, IDefaultBrowserLayer,
    ...      IBrowserView, ILeftColumn),
    ...     IViewlet, name='third')

Now there should be some viewlets.

    >>> manager.update()
    >>> manager.render()
    u'first\nsecond\nthird'

Now we should be able to change the order by setting it in the storage.

    >>> storage.setOrder('left', 'Plone Default', ('third','first','second'))

    >>> manager.update()
    >>> manager.render()
    u'third\nfirst\nsecond'

The default skin should now be that same one for that manager.

    >>> storage.getDefault('left')
    'Plone Default'

If we change the skin, the default order should apply.

    >>> content.skin = 'MySkin'

    >>> manager.update()
    >>> manager.render()
    u'third\nfirst\nsecond'

    >>> del content.skin

We can also hide viewlets.

    >>> storage.setHidden('left', 'Plone Default', ('first',))

    >>> manager.update()
    >>> manager.render()
    u'third\nsecond'
