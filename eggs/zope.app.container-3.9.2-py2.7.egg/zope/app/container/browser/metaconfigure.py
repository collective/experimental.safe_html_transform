##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Container-specific browser ZCML namespace directive handlers
"""

__docformat__ = 'restructuredtext'

from zope.interface import Interface
from zope.component import queryMultiAdapter
from zope.configuration.fields import GlobalObject, GlobalInterface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.security.zcml import Permission
from zope.browserpage.metaconfigure import page, view
from zope.browsermenu.metaconfigure import menuItemDirective
from zope.app.container.browser.contents import Contents
from zope.app.container.browser.adding import Adding
from zope.app.container.i18n import ZopeMessageFactory as _


class IContainerViews(Interface):
    """Define several container views for an `IContainer` implementation."""

    for_ = GlobalObject(
        title=u"The declaration this containerViews are for.",
        description=u"""
        The containerViews will be available for all objects that
        provide this declaration.
        """,
        required=True)

    contents = Permission(
        title=u"The permission needed for content page.",
        required=False)

    index = Permission(
        title=u"The permission needed for index page.",
        required=False)

    add = Permission(
        title=u"The permission needed for add page.",
        required=False)

    layer = GlobalInterface(
        title=_("The layer the view is in."),
        description=_("""A skin is composed of layers. It is common to put
        skin specific views in a layer named after the skin. If the 'layer'
        attribute is not supplied, it defaults to 'default'."""),
        required=False
        )


def containerViews(_context, for_, contents=None, add=None, index=None,
                   layer=IDefaultBrowserLayer):
    """Set up container views for a given content type."""

    if for_ is None:
            raise ValueError("A for interface must be specified.")

    if contents is not None:
        from zope.app.menus import zmi_views
        page(_context, name='contents.html', permission=contents,
             for_=for_, layer=layer, class_=Contents, attribute='contents',
             menu=zmi_views, title=_('Contents'))

    if index is not None:
        page(_context, name='index.html', permission=index, for_=for_,
             layer=layer, class_=Contents, attribute='index')

    if add is not None:
        from zope.app.menus import zmi_actions
        viewObj = view(_context, name='+', layer=layer, for_=for_,
                       permission=add, class_=Adding)
        menuItemDirective(
            _context, zmi_actions, for_, '+', _('Add'), permission=add, layer=layer,
            filter='python:modules["zope.app.container.browser.metaconfigure"].menuFilter(context, request)')
        viewObj.page(_context, name='index.html', attribute='index')
        viewObj.page(_context, name='action.html', attribute='action')
        viewObj()

def menuFilter(context, request):
    '''This is a function that filters the "Add" menu item'''
    adding = queryMultiAdapter((context, request), name="+")
    if adding is None:
        adding = Adding(context, request)
    adding.__parent__ = context
    adding.__name__ = '+'
    info = adding.addingInfo()
    return bool(info)
