# -*- coding: utf-8 -*-
# $Id: interfaces.py 246084 2011-11-01 22:45:18Z glenfant $
"""Public interfaces"""

from zope.interface import Interface


class IControlPanel(Interface):
    """ZCML documentation Control Panel
    """
    def namespaces():
        """Ordered list of dicts with keys
        * namespace: URI of namespace
        * view_url: URL to the details
        """


class IControlPanelBrowserRequest(Interface):
    """We mark the request with this interface to have a chance to force the
    publication language throug our special language negociator.  """
