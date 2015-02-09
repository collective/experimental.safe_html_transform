# -*- coding: utf-8 -*-
# BaseTestCase

from Products.CMFTestCase.ctc import CMFTestCase
from Products.CMFTestCase.ctc import setupCMFSite
from Products.CMFTestCase.ctc import installProduct

setupCMFSite(extension_profiles=['Products.CMFDiffTool:CMFDiffTool'])

class BaseTestCase(CMFTestCase):
    """This is a stub now, but in case you want to try
       something fancy on Your Branch (tm), put it here.
    """


try:
    from archetypes import schemaextender
    HAS_AT_SCHEMA_EXTENDER = True
except ImportError:
    HAS_AT_SCHEMA_EXTENDER = False
try:
    from Products.Five import fiveconfigure, zcml
    from Products.PloneTestCase import PloneTestCase as ptc
    from Products.PloneTestCase.layer import PloneSite
    HAS_PLONE = True
except ImportError:
    HAS_PLONE = False

if HAS_PLONE:
    class CMFDiffToolLayer(PloneSite):
        @classmethod
        def setUp(cls):
            """Set up additional products and ZCML required to test
            this product.
            """
            ptc.setupPloneSite()
            installProduct('CMFDiffTool')
            if HAS_AT_SCHEMA_EXTENDER:
                zcml.load_config('configure.zcml', schemaextender)
            PloneSite.setUp()


    class ATBaseTestCase(ptc.PloneTestCase):
        """
        For tests that need archetypes
        """
        layer = CMFDiffToolLayer
