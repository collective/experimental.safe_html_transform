from zope.component import adapter, queryUtility
from zope.annotation.interfaces import IAnnotations

from zope.globalrequest import getRequest

from z3c.caching.interfaces import IPurgeEvent

from plone.registry.interfaces import IRegistry

from plone.cachepurging.interfaces import ICachePurgingSettings
from plone.cachepurging.interfaces import IPurger

from plone.cachepurging.utils import getPathsToPurge
from plone.cachepurging.utils import isCachePurgingEnabled
from plone.cachepurging.utils import getURLsToPurge

from ZPublisher.interfaces import IPubSuccess

KEY = "plone.cachepurging.urls"

@adapter(IPurgeEvent)
def queuePurge(event):
    """Find URLs to purge and queue them for later
    """

    request = getRequest()
    if request is None:
        return

    annotations = IAnnotations(request, None)
    if annotations is None:
        return

    if not isCachePurgingEnabled():
        return

    paths = annotations.setdefault(KEY, set())
    paths.update(getPathsToPurge(event.object, request))

@adapter(IPubSuccess)
def purge(event):
    """Asynchronously send PURGE requests
    """

    request = event.request

    annotations = IAnnotations(request, None)
    if annotations is None:
        return

    paths = annotations.get(KEY, None)
    if paths is None:
        return

    registry = queryUtility(IRegistry)
    if registry is None:
        return

    if not isCachePurgingEnabled(registry=registry):
        return

    purger = queryUtility(IPurger)
    if purger is None:
        return

    settings = registry.forInterface(ICachePurgingSettings, check=False)
    for path in paths:
        for url in getURLsToPurge(path, settings.cachingProxies):
            purger.purgeAsync(url)
