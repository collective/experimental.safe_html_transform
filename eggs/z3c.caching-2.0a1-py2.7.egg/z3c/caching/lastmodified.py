from zope.interface import implementer
from zope.component import adapter

from zope.browser.interfaces import IView
from z3c.caching.interfaces import ILastModified

@implementer(ILastModified)
@adapter(IView)
def viewDelegateLastModified(view):
    """When looking up an ILastModified for a view, look up an ILastModified
    for its context. May return None, in which case adaptation will fail.
    """
    return ILastModified(view.context, None)
