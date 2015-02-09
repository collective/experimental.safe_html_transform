try:
    from Products.CMFDefault.interfaces import ICMFDefaultSkin as IDefaultBrowserLayer
except ImportError:
    from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IDefaultPloneLayer(IDefaultBrowserLayer):
    """A Zope 3 browser layer corresponding to Plone defaults
    """
