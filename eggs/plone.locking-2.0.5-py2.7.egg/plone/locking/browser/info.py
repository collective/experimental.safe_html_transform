from zope.interface import implements
from zope.component import getMultiAdapter

from zope.viewlet.interfaces import IViewlet

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class LockInfoViewlet(BrowserView):
    """This is a viewlet which is not hooked up anywhere. It is referenced
    from plone.app.layout. We do it this way to avoid having the  lower-level
    plone.locking depend on these packages, whilst still providing
    an implementation of the info box in a single place.
    """
    implements(IViewlet)

    template = ViewPageTemplateFile('info.pt')

    def __init__(self, context, request, view, manager):
        super(LockInfoViewlet, self).__init__(context, request)
        self.__parent__ = view
        self.context = context
        self.request = request
        self.view = view
        self.manager = manager
        self.info = getMultiAdapter((context, request), name="plone_lock_info")

    def update(self):
        pass

    def render(self):
        return self.template()

    def lock_is_stealable(self):
        return self.info.lock_is_stealable()

    def lock_info(self):
        return self.info.lock_info()
