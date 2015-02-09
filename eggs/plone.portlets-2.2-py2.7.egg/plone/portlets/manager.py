import logging

from plone.memoize.view import memoize
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.component import getUtilitiesFor
from zope.contentprovider.interfaces import UpdateNotCalled
from zope.interface import implements
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserView
from zope.publisher.interfaces.browser import IBrowserRequest
from ZODB.POSException import ConflictError

from plone.portlets.interfaces import IPortletRetriever
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletManagerRenderer
from plone.portlets.interfaces import IPortletRenderer
from plone.portlets.interfaces import IPortletType
from plone.portlets.storage import PortletStorage
from plone.portlets.utils import hashPortletInfo

logger = logging.getLogger('portlets')


class PortletManagerRenderer(object):
    """Default renderer for portlet managers.

    When the zope.contentprovider handler for the provider: expression looks up
    a name, context, it will find an adapter factory that in turn finds an
    instance of this class, by doing an adapter lookup for (context, request,
    view, manager).
    """
    implements(IPortletManagerRenderer)
    adapts(Interface, IBrowserRequest, IBrowserView, IPortletManager)

    template = None
    error_message = None

    def __init__(self, context, request, view, manager):
        self.__parent__ = view
        self.manager = manager # part of interface
        self.context = context
        self.request = request
        self.__updated = False

    @property
    def visible(self):
        portlets = self.portletsToShow()
        return len(portlets) > 0

    def filter(self, portlets):
        filtered = []
        for p in portlets:
            try:
                if p['assignment'].available:
                    filtered.append(p)
            except ConflictError:
                raise
            except Exception, e:
                logger.exception(
                    "Error while determining assignment availability of "
                    "portlet (%r %r %r): %s" % (
                    p['category'], p['key'], p['name'], str(e)))
        return filtered

    def portletsToShow(self):
        return [p for p in self.allPortlets() if p['available']]

    def allPortlets(self):
        return self._lazyLoadPortlets(self.manager)

    def update(self):
        self.__updated = True
        for p in self.portletsToShow():
            p['renderer'].update()

    def render(self):
        if not self.__updated:
            raise UpdateNotCalled

        portlets = self.portletsToShow()
        if self.template:
            return self.template(portlets=portlets)
        else:
            return u'\n'.join([p['renderer'].render() for p in portlets])

    def safe_render(self, portlet_renderer):
        try:
            return portlet_renderer.render()
        except ConflictError:
            raise
        except Exception:
            logger.exception('Error while rendering %r' % (self, ))
            return self.error_message()

    # Note: By passing in a parameter that's different for each portlet
    # manager, we avoid the view memoization (which is tied to the request)
    # caching the same portlets for all managers on the page. We cache the
    # portlets using a view memo because it they be looked up multiple times,
    # e.g. first to check if portlets should be displayed and later to
    # actually render

    @memoize
    def _lazyLoadPortlets(self, manager):
        retriever = getMultiAdapter((self.context, manager), IPortletRetriever)
        items = []
        for p in self.filter(retriever.getPortlets()):
            renderer = self._dataToPortlet(p['assignment'].data)
            info = p.copy()
            info['manager'] = self.manager.__name__
            info['renderer'] = renderer
            hashPortletInfo(info)
            # Record metadata on the renderer
            renderer.__portlet_metadata__ = info.copy()
            del renderer.__portlet_metadata__['renderer']
            try:
                isAvailable = renderer.available
            except ConflictError:
                raise
            except Exception, e:
                isAvailable = False
                logger.exception(
                    "Error while determining renderer availability of portlet "
                    "(%r %r %r): %s" % (
                    p['category'], p['key'], p['name'], str(e)))

            info['available'] = isAvailable
            items.append(info)

        return items

    def _dataToPortlet(self, data):
        """Helper method to get the correct IPortletRenderer for the given
        data object.
        """
        return getMultiAdapter((self.context, self.request, self.__parent__,
                                self.manager, data, ), IPortletRenderer)


class PortletManager(PortletStorage):
    """Default implementation of the portlet manager.

    Provides the functionality that allows the portlet manager to act as an
    adapter factory.
    """

    implements(IPortletManager)

    __name__ = __parent__ = None

    def __call__(self, context, request, view):
        return getMultiAdapter((context, request, view, self),
                               IPortletManagerRenderer)

    def getAddablePortletTypes(self):
        addable = []
        for p in getUtilitiesFor(IPortletType):
            # BBB - first condition, because starting with Plone 3.1
            #every p[1].for_ should be a list
            if not isinstance(p[1].for_, list):
                logger.warning("Deprecation Warning Portlet type %s is using "
                    "a deprecated format for storing interfaces of portlet "
                    "managers where it is addable. Its for_ attribute should "
                    "be a list of portlet manager interfaces, using "
                    "[zope.interface.Interface] for the portlet type to be "
                    "addable anywhere. The old format will be unsupported in "
                    " Plone 4.0." % p[1].addview)
                if p[1].for_ is None or p[1].for_.providedBy(self):
                    addable.append(p[1])
            elif [i for i in p[1].for_ if i.providedBy(self)]:
                addable.append(p[1])
        return addable
