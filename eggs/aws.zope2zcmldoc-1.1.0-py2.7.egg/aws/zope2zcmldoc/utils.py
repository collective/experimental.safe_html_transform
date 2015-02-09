# -*- coding: utf-8 -*-
# $Id: utils.py 246084 2011-11-01 22:45:18Z glenfant $
"""Misc utilities"""

from zope.interface import implements
from zope.component import adapts

from zope.i18n.interfaces import IUserPreferredLanguages
from Products.Five import BrowserView
from config import CONTROLPANEL_ID
from controlpanel import ControlPanel
from aws.zope2zcmldoc.interfaces import IControlPanelBrowserRequest
from aws.zope2zcmldoc import awsZope2zcmldocMF as _

try:
    from Products.PlacelessTranslationService.Negotiator import PTSLanguages
except ImportError:
    class PTSLanguages(object):
        """Minimal PTS like language negociator
        """
        implements(IUserPreferredLanguages)

        def __init__(self, context):
            self.context = context

        def getPreferredLanguages(self):
            return ['en']


class Languages(PTSLanguages):
    """Adapts requests marked with ``IControlPanelBrowserRequest``
    to allow forcing english language by extending the URL with
    ``?forced_en:boolean=True``.
    """
    adapts(IControlPanelBrowserRequest)

    def getPreferredLanguages(self):
        """See IUserPreferredLanguages
        (for a reason I can't understand, the request is in the ``self.context``
        attribute). See PTS source.
        """
        forced_en = self.context.get('forced_en', False)
        if forced_en:
            return ['en']
        return super(Languages, self).getPreferredLanguages()


class Utils(BrowserView):
    """(Un)installs the control panel
    """
    def install(self):
        """Add the control panel
        """
        zcp = self.context.Control_Panel
        if CONTROLPANEL_ID not in zcp.objectIds():
            mpcp = ControlPanel()
            zcp._setObject(CONTROLPANEL_ID, mpcp)
        return _(u"ZCML doc panel added. Click the 'Back' button of your browser.")

    def uninstall(self):
        """Removes the control panel
        """
        zcp = self.context.Control_Panel
        if CONTROLPANEL_ID in zcp.objectIds():
            zcp._delObject(CONTROLPANEL_ID)
        return _(u"ZCML doc panel removed. Click the 'Back' button of your browser.")
