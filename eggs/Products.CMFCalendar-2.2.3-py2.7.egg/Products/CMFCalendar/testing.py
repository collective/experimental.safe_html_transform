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
""" Unit test layers.

$Id: testing.py 114573 2010-07-11 10:55:06Z hannosch $
"""

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
        import Products.CMFCalendar
        import Products.CMFDefault
        import Products.DCWorkflow
        import OFS

        zcml.load_config('configure.zcml', Products.CMFCalendar)
        zcml.load_config('configure.zcml', Products.CMFDefault)
        zcml.load_config('configure.zcml', Products.DCWorkflow)

        try:
            zcml.load_config('meta.zcml', OFS)
            zcml.load_config('configure.zcml', OFS)
        except IOError:  # Zope <= 2.13.0a2
            pass
        ZopeTestCase.installPackage('OFS')

        app = ZopeTestCase.app()
        addConfiguredSite(app, 'site', 'Products.CMFDefault:default',
                          snapshot=False,
                          extension_ids=('Products.CMFCalendar:default',
                                        'Products.CMFCalendar:skins_support'))
        transaction.commit()
        ZopeTestCase.close(app)

    @classmethod
    def tearDown(cls):
        app = ZopeTestCase.app()
        app._delObject('site')
        transaction.commit()
        ZopeTestCase.close(app)
