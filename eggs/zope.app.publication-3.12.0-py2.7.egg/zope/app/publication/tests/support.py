# an API to help us do some component registrations for
# the publisher to help with the testing.
# This functionality is also implemented in zope.app.testing.
# this functionality has two problems:
# * the code is extremely hard to understand as it papers over
#   the zope.component APIs
# * we want to lift the dependency on zope.app.testing for other reasons
# it's possible that this code should end up in published test support modules
# in other packages deeper down (zope.publisher, zope.traversing). The
# fact that we have to import interfaces from these gives us this
# clue. We will investigate pushing them down to these packages
# later.
from zope import component
from zope.traversing.interfaces import ITraversable
from zope.publisher.interfaces import IDefaultViewName
from zope.publisher.interfaces.browser import (IDefaultBrowserLayer,
                                               IBrowserRequest)

def provideNamespaceHandler(name, handler):
    component.provideAdapter(handler, (None,), ITraversable,
                             name=name)
    component.provideAdapter(handler, (None, None), ITraversable,
                             name=name)

def setDefaultViewName(for_, name, layer=IDefaultBrowserLayer,
                       type=IBrowserRequest):
    if layer is None:
        layer = type
    component.provideAdapter(name, (for_, layer), IDefaultViewName)
