# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('experimental.safe_html_transform')


class IExperimentalSafeHtmlTransformLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""
