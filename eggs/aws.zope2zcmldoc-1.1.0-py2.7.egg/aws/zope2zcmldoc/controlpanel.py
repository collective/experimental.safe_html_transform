# -*- coding: utf-8 -*-
# $Id: controlpanel.py 246098 2011-11-02 10:10:59Z glenfant $
"""Our Zope 2 ZMI control panel"""

import Acquisition
from OFS import SimpleItem
from zope.interface import implements
from zope.configuration.docutils import makeDocStructures

from aws.zope2zcmldoc import awsZope2zcmldocMF as _
from config import CONTROLPANEL_ID, ZOPE_VERSION
from interfaces import IControlPanel

if ZOPE_VERSION > (2, 12):
    class Fake:
        pass
else:
    from App.ApplicationManager import Fake


doc_namespaces = None
doc_subdirs = None


class ControlPanel(Fake, SimpleItem.Item, Acquisition.Implicit):
    """The Monkey patches control panel"""

    implements(IControlPanel)
    id = CONTROLPANEL_ID
    name = title = _("ZCML Documentation")
    #manage_main = PageTemplateFile('zmi/controlpanel.pt', globals())

    manage_options = ((
        {'label': _('ZCML documentation'), 'action': 'manage_main'},
        ))

    def getId(self):
        """Required by ZMI
        """
        return self.id

    def getNamespaces(self):
        global doc_namespaces, doc_subdirs
        if doc_namespaces is None:
            doc_namespaces, doc_subdirs = makeDocStructures(self._getContext())
        return doc_namespaces

    def getSubdirs(self):
        global doc_namespaces, doc_subdirs
        if doc_subdirs is None:
            doc_namespaces, doc_subdirs = makeDocStructures(self._getContext())
        return doc_subdirs

    def _getContext(self):
        """ZCML context
        """
        if ZOPE_VERSION > (2, 13):
            from Zope2.App.zcml import _context
        else:
            from Products.Five.zcml import _context
        return _context
