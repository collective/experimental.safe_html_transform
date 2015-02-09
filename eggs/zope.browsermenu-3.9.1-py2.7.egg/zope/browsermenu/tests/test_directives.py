##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""'browser' namespace directive tests

$Id: test_directives.py 111004 2010-04-16 20:13:36Z tseaver $
"""

import sys
import os
import unittest
from cStringIO import StringIO
from doctest import DocTestSuite

from zope import component
from zope.interface import Interface, implements, directlyProvides, providedBy

import zope.security.management
from zope.configuration.xmlconfig import xmlconfig, XMLConfig
from zope.configuration.exceptions import ConfigurationError
from zope.publisher.browser import TestRequest
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.browser import IBrowserSkinType
from zope.security.proxy import removeSecurityProxy, ProxyFactory
from zope.security.permission import Permission
from zope.security.interfaces import IPermission
from zope.traversing.adapters import DefaultTraversable
from zope.traversing.interfaces import ITraversable

import zope.browsermenu
from zope.component.testfiles.views import IC, V1, VZMI, R1, IV
from zope.browsermenu.menu import getFirstMenuItem, BrowserMenu
from zope.browsermenu.interfaces import IMenuItemType, IBrowserMenu
from zope.testing import cleanup

tests_path = os.path.join(
    os.path.dirname(zope.browsermenu.__file__),
    'tests')

template = """<configure
   xmlns='http://namespaces.zope.org/zope'
   xmlns:browser='http://namespaces.zope.org/browser'
   i18n_domain='zope'>
   %s
   </configure>"""


request = TestRequest()

class M1(BrowserMenu):
    pass

class V2(V1, object):

    def action(self):
        return self.action2()

    def action2(self):
        return "done"

class VT(V1, object):
    def publishTraverse(self, request, name):
        try:
            return int(name)
        except:
            return super(VT, self).publishTraverse(request, name)

class Ob(object):
    implements(IC)

ob = Ob()

class NCV(object):
    "non callable view"

    def __init__(self, context, request):
        pass

class CV(NCV):
    "callable view"
    def __call__(self):
        pass


class C_w_implements(NCV):
    implements(Interface)

    def index(self):
        return self

class ITestMenu(Interface):
    """Test menu."""

directlyProvides(ITestMenu, IMenuItemType)


class ITestLayer(IBrowserRequest):
    """Test Layer."""

class ITestSkin(ITestLayer):
    """Test Skin."""


class MyResource(object):

    def __init__(self, request):
        self.request = request


class Test(cleanup.CleanUp, unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp()
        XMLConfig('meta.zcml', zope.browsermenu)()
        component.provideAdapter(DefaultTraversable, (None,), ITraversable)

    def tearDown(self):
        if 'test_menu' in dir(sys.modules['zope.app.menus']):
            delattr(sys.modules['zope.app.menus'], 'test_menu')
        super(Test, self).tearDown()

    def testMenuOverride(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu" />
            <browser:menuItem
                action="@@test"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                menu="test_menu"
                title="Test View"
                />
            '''
            )))
        menu1 = component.getUtility(IBrowserMenu, 'test_menu')
        menuItem1 = getFirstMenuItem('test_menu', ob, TestRequest())
        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu"
                class="zope.browsermenu.tests.test_directives.M1" />
            '''
            )))
        menu2 = component.getUtility(IBrowserMenu, 'test_menu')
        menuItem2 = getFirstMenuItem('test_menu', ob, TestRequest())
        self.assertNotEqual(menu1, menu2)
        self.assertEqual(menuItem1, menuItem2)


    def testMenuItemNeedsFor(self):
        # <browser:menuItem> directive fails if no 'for' argument was provided
        from zope.configuration.exceptions import ConfigurationError
        self.assertRaises(ConfigurationError, xmlconfig, StringIO(template %
            '''
            <browser:menu
                id="test_menu" title="Test menu" />
            <browser:menuItem
                title="Test Entry"
                menu="test_menu"
                action="@@test"
            />
            '''
            ))

	    # it works, when the argument is there and a valid interface
        xmlconfig(StringIO(template %
            '''
            <browser:menuItem
                for="zope.component.testfiles.views.IC"
                title="Test Entry"
                menu="test_menu"
                action="@@test"
            />
            '''
            ))

def test_suite():
    return unittest.makeSuite(Test)
