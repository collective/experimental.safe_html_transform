from zope.component import queryUtility
from zope.interface import Interface
try:
    from plone.app.redirector.interfaces import IRedirectionStorage
    IRedirectionStorage  # pyflakes
except ImportError:
    IRedirectionStorage = None


class MarkerInterface(Interface):
    pass


def get_redirects(new_object):
    """Get p.a.redirector redirects.

    Maybe this is also used outside of Plone, or p.a.redirector is
    optional, so try not to fail too hard then.

    The tests will currently fail in that case.  If wanted, we could
    arrange something here, for example letting add_redirects return
    the a list of successfully stored redirects, which would be an
    empty list when p.a.redirector is not there, and letting
    get_redirects return an empty list.
    """
    if IRedirectionStorage is None:
        return
    storage = queryUtility(IRedirectionStorage)
    if storage is None:
        return
    path = '/'.join(new_object.getPhysicalPath())
    return storage.redirects(path)


def add_redirects(old_paths, new_object):
    """Add p.a.redirector redirects.

    Maybe this is also used outside of Plone, or p.a.redirector is
    optional, so try not to fail too hard then.
    """
    if IRedirectionStorage is None:
        return
    storage = queryUtility(IRedirectionStorage)
    if storage is None:
        return
    path = '/'.join(new_object.getPhysicalPath())
    for redirect in old_paths:
        storage.add(redirect, path)
