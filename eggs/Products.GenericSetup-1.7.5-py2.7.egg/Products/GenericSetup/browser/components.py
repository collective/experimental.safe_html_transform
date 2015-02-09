##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Components setup view.
"""

import os.path

import zope.formlib
from Products.Five.browser.decode import processInputs
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.component.interfaces import IObjectManagerSite
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.formlib import form
from zope.interface import implements
from zope.interface import Interface
from zope.schema import Text
from ZPublisher import HTTPRequest

from Products.GenericSetup.context import SetupEnviron
from Products.GenericSetup.interfaces import IBody

_FORMLIB_DIR = os.path.dirname(zope.formlib.__file__)
_PAGEFORM_PATH = os.path.join(_FORMLIB_DIR, 'pageform.pt')


class IComponentsSetupSchema(Interface):

    """Schema for components setup views.
    """

    body = Text(
        title=u'Settings')


class ComponentsSetupSchemaAdapter(object):

    adapts(IObjectManagerSite)
    implements(IComponentsSetupSchema)

    def __init__(self, context):
        self.context = context

    def _getBody(self):
        sm = self.context.aq_inner.getSiteManager()
        return getMultiAdapter((sm, SetupEnviron()), IBody).body

    def _setBody(self, value):
        sm = self.context.aq_inner.getSiteManager()
        getMultiAdapter((sm, SetupEnviron()), IBody).body = value

    body = property(_getBody, _setBody)


class ComponentsSetupView(form.PageEditForm):

    """Components setup view for IObjectManagerSite.
    """

    template = ViewPageTemplateFile(_PAGEFORM_PATH)

    label = u'Component Registry: XML Configuration'

    form_fields = form.FormFields(IComponentsSetupSchema)

    def update(self):
        # BBB: for Zope < 2.14
        if not getattr(self.request, 'postProcessInputs', False):
            processInputs(self.request, [HTTPRequest.default_encoding])
        super(ComponentsSetupView, self).update()

    def setUpWidgets(self, ignore_request=False):
        super(ComponentsSetupView,
              self).setUpWidgets(ignore_request=ignore_request)
        self.widgets['body'].height = 24


class ComponentsSetupTab(ComponentsSetupView):

    """Components setup ZMI tab for IObjectManagerSite.
    """

    base_template = ComponentsSetupView.template

    template = ViewPageTemplateFile('components.pt')

    label = None
