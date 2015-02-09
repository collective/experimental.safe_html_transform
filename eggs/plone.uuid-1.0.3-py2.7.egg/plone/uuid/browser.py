from zope.publisher.browser import BrowserView
from plone.uuid.interfaces import IUUID


class UUIDView(BrowserView):
    """A simple browser view that renders the UUID of its context
    """

    def __call__(self):
        return unicode(IUUID(self.context, u""))
