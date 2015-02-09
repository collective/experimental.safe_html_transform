##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit test layers. """

from Testing import ZopeTestCase
ZopeTestCase.installProduct('ZCTextIndex', 1)
ZopeTestCase.installProduct('CMFCore', 1)

import transaction

from Products.CMFCore.testing import FunctionalZCMLLayer
from Products.CMFDefault.factory import addConfiguredSite

# BBB for Zope 2.12
try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml


class FunctionalLayer(FunctionalZCMLLayer):

    @classmethod
    def setUp(cls):
        import Products.CMFDefault
        import Products.DCWorkflow

        zcml.load_config('configure.zcml', Products.CMFDefault)
        zcml.load_config('configure.zcml', Products.DCWorkflow)

        app = ZopeTestCase.app()
        addConfiguredSite(app, 'site', 'Products.CMFDefault:default',
                          snapshot=False)
        transaction.commit()
        ZopeTestCase.close(app)

    @classmethod
    def tearDown(cls):
        app = ZopeTestCase.app()
        app._delObject('site')
        transaction.commit()
        ZopeTestCase.close(app)

