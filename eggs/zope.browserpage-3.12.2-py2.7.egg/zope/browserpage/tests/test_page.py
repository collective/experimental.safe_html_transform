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
"""Tests for browser:page directive and friends

$Id: test_page.py 111996 2010-05-05 17:34:04Z tseaver $
"""

import sys
import os
import unittest
from doctest import DocTestSuite
from cStringIO import StringIO

from zope import component
from zope.interface import Interface, implements, directlyProvides, providedBy

import zope.security.management
from zope.configuration.xmlconfig import xmlconfig, XMLConfig
from zope.configuration.exceptions import ConfigurationError
from zope.publisher.browser import TestRequest
from zope.publisher.interfaces import IDefaultViewName
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.browser import IBrowserSkinType, IDefaultSkin
from zope.security.proxy import removeSecurityProxy, ProxyFactory
from zope.security.permission import Permission
from zope.security.interfaces import IPermission
from zope.testing import cleanup
from zope.traversing.adapters import DefaultTraversable
from zope.traversing.interfaces import ITraversable

import zope.publisher.defaultview
import zope.browserpage
import zope.browsermenu
from zope.browsermenu.menu import getFirstMenuItem
from zope.browsermenu.interfaces import IMenuItemType
from zope.component.testfiles.views import IC, V1, VZMI, R1, IV

tests_path = os.path.dirname(__file__)

template = """<configure
   xmlns='http://namespaces.zope.org/zope'
   xmlns:browser='http://namespaces.zope.org/browser'
   i18n_domain='zope'>
   %s
   </configure>"""

class templateclass(object):
    def data(self): return 42

request = TestRequest()

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

class ITestLayer(IBrowserRequest):
    """Test Layer."""

class ITestSkin(ITestLayer):
    """Test Skin."""


class ITestMenu(Interface):
    """Test menu."""

directlyProvides(ITestMenu, IMenuItemType)

class Test(cleanup.CleanUp, unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp()
        XMLConfig('meta.zcml', zope.browserpage)()
        XMLConfig('meta.zcml', zope.browsermenu)()
        component.provideAdapter(DefaultTraversable, (None,), ITraversable, )
        zope.security.management.newInteraction()

    def testPage(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template % (
            '''
            <browser:page
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                attribute="index"
                />
            '''
            )))

        v = component.queryMultiAdapter((ob, request), name='test')
        self.assert_(issubclass(v.__class__, V1))


    def testPageWithClassWithMenu(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        testtemplate = os.path.join(tests_path, 'testfiles', 'test.pt')


        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu" />
            <browser:page
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                template="%s"
                menu="test_menu"
                title="Test View"
                />
            ''' % testtemplate
            )))
        menuItem = getFirstMenuItem('test_menu', ob, TestRequest())
        self.assertEqual(menuItem["title"], "Test View")
        self.assertEqual(menuItem["action"], "@@test")
        v = component.queryMultiAdapter((ob, request), name='test')
        self.assertEqual(v(), "<html><body><p>test</p></body></html>\n")


    def testPageWithTemplateWithMenu(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        testtemplate = os.path.join(tests_path, 'testfiles', 'test.pt')

        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu"/>
            <browser:page
                name="test"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                template="%s"
                menu="test_menu"
                title="Test View"
                />
            ''' % testtemplate
            )))

        menuItem = getFirstMenuItem('test_menu', ob, TestRequest())
        self.assertEqual(menuItem["title"], "Test View")
        self.assertEqual(menuItem["action"], "@@test")
        v = component.queryMultiAdapter((ob, request), name='test')
        self.assertEqual(v(), "<html><body><p>test</p></body></html>\n")


    def testPageInPagesWithTemplateWithMenu(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        testtemplate = os.path.join(tests_path, 'testfiles', 'test.pt')

        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu" />
            <browser:pages
                for="zope.component.testfiles.views.IC"
                permission="zope.Public">
              <browser:page
                  name="test"
                  template="%s"
                  menu="test_menu"
                  title="Test View"
                  />
            </browser:pages>
            ''' % testtemplate
            )))

        menuItem = getFirstMenuItem('test_menu', ob, TestRequest())
        self.assertEqual(menuItem["title"], "Test View")
        self.assertEqual(menuItem["action"], "@@test")
        v = component.queryMultiAdapter((ob, request), name='test')
        self.assertEqual(v(), "<html><body><p>test</p></body></html>\n")


    def testPageInPagesWithClassWithMenu(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        testtemplate = os.path.join(tests_path, 'testfiles', 'test.pt')

        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu" />
            <browser:pages
                for="zope.component.testfiles.views.IC"
                class="zope.component.testfiles.views.V1"
                permission="zope.Public">
              <browser:page
                  name="test"
                  template="%s"
                  menu="test_menu"
                  title="Test View"
                  />
            </browser:pages>
            ''' % testtemplate
            )))

        menuItem = getFirstMenuItem('test_menu', ob, TestRequest())
        self.assertEqual(menuItem["title"], "Test View")
        self.assertEqual(menuItem["action"], "@@test")
        v = component.queryMultiAdapter((ob, request), name='test')
        self.assertEqual(v(), "<html><body><p>test</p></body></html>\n")

    def testSkinPage(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template % (
            '''
            <browser:page name="test"
                class="zope.component.testfiles.views.VZMI"
                layer="
                  zope.browserpage.tests.test_page.ITestLayer"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                attribute="index"
                />
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                attribute="index"
                />
            '''
            )))

        v = component.queryMultiAdapter((ob, request), name='test')
        self.assert_(issubclass(v.__class__, V1))
        v = component.queryMultiAdapter(
            (ob, TestRequest(skin=ITestSkin)), name='test')
        self.assert_(issubclass(v.__class__, VZMI))


    def testInterfaceProtectedPage(self):
        xmlconfig(StringIO(template %
            '''
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                attribute="index"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                allowed_interface="zope.component.testfiles.views.IV"
                />
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        v = ProxyFactory(v)
        self.assertEqual(v.index(), 'V1 here')
        self.assertRaises(Exception, getattr, v, 'action')

    def testAttributeProtectedPage(self):
        xmlconfig(StringIO(template %
            '''
            <browser:page name="test"
                class="zope.browserpage.tests.test_page.V2"
                for="zope.component.testfiles.views.IC"
                attribute="action"
                permission="zope.Public"
                allowed_attributes="action2"
                />
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        v = ProxyFactory(v)
        self.assertEqual(v.action(), 'done')
        self.assertEqual(v.action2(), 'done')
        self.assertRaises(Exception, getattr, v, 'index')

    def testAttributeProtectedView(self):
        xmlconfig(StringIO(template %
            '''
            <browser:view name="test"
                class="zope.browserpage.tests.test_page.V2"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                allowed_attributes="action2"
                >
              <browser:page name="index.html" attribute="action" />
           </browser:view>
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        v = ProxyFactory(v)
        page = v.publishTraverse(request, 'index.html')
        self.assertEqual(page(), 'done')
        self.assertEqual(v.action2(), 'done')
        self.assertRaises(Exception, getattr, page, 'index')

    def testInterfaceAndAttributeProtectedPage(self):
        xmlconfig(StringIO(template %
            '''
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                attribute="index"
                allowed_attributes="action"
                allowed_interface="zope.component.testfiles.views.IV"
                />
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        self.assertEqual(v.index(), 'V1 here')
        self.assertEqual(v.action(), 'done')

    def testDuplicatedInterfaceAndAttributeProtectedPage(self):
        xmlconfig(StringIO(template %
            '''
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                attribute="index"
                permission="zope.Public"
                allowed_attributes="action index"
                allowed_interface="zope.component.testfiles.views.IV"
                />
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        self.assertEqual(v.index(), 'V1 here')
        self.assertEqual(v.action(), 'done')

    def test_class_w_implements(self):
        xmlconfig(StringIO(template %
            '''
            <browser:page
                name="test"
                class="
             zope.browserpage.tests.test_page.C_w_implements"
                for="zope.component.testfiles.views.IC"
                attribute="index"
                permission="zope.Public"
                />
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        self.assertEqual(v.index(), v)
        self.assert_(IBrowserPublisher.providedBy(v))

    def testIncompleteProtectedPageNoPermission(self):
        self.assertRaises(
            ConfigurationError,
            xmlconfig,
            StringIO(template %
            '''
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                attribute="index"
                allowed_attributes="action index"
                />
            '''
            ))


    def testPageViews(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        test3 = os.path.join(tests_path, 'testfiles', 'test3.pt')

        xmlconfig(StringIO(template %
            '''
            <browser:pages
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >

              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
              <browser:page name="test.html" template="%s" />
            </browser:pages>
            ''' % test3
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        self.assertEqual(v(), 'V1 here')
        v = component.getMultiAdapter((ob, request), name='action.html')
        self.assertEqual(v(), 'done')
        v = component.getMultiAdapter((ob, request), name='test.html')
        self.assertEqual(str(v()), '<html><body><p>done</p></body></html>\n')

    def testNamedViewPageViewsCustomTraversr(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.browserpage.tests.test_page.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >

              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
            </browser:view>
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        self.assertEqual(view.browserDefault(request)[1], (u'index.html', ))


        v = view.publishTraverse(request, 'index.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'V1 here')
        v = view.publishTraverse(request, 'action.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'done')


    def testNamedViewNoPagesForCallable(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.browserpage.tests.test_page.CV"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                />
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        self.assertEqual(view.browserDefault(request), (view, ()))

    def testNamedViewNoPagesForNonCallable(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.browserpage.tests.test_page.NCV"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                />
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        self.assertEqual(getattr(view, 'browserDefault', None), None)

    def testNamedViewPageViewsNoDefault(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        test3 = os.path.join(tests_path, 'testfiles', 'test3.pt')

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >

              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
              <browser:page name="test.html" template="%s" />
            </browser:view>
            ''' % test3
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        self.assertEqual(view.browserDefault(request)[1], (u'index.html', ))


        v = view.publishTraverse(request, 'index.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'V1 here')
        v = view.publishTraverse(request, 'action.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'done')
        v = view.publishTraverse(request, 'test.html')
        v = removeSecurityProxy(v)
        self.assertEqual(str(v()), '<html><body><p>done</p></body></html>\n')

    def testNamedViewPageViewsWithDefault(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        test3 = os.path.join(tests_path, 'testfiles', 'test3.pt')

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >

              <browser:defaultPage name="test.html" />
              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
              <browser:page name="test.html" template="%s" />
            </browser:view>
            ''' % test3
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        self.assertEqual(view.browserDefault(request)[1], (u'test.html', ))


        v = view.publishTraverse(request, 'index.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'V1 here')
        v = view.publishTraverse(request, 'action.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'done')
        v = view.publishTraverse(request, 'test.html')
        v = removeSecurityProxy(v)
        self.assertEqual(str(v()), '<html><body><p>done</p></body></html>\n')

    def testTraversalOfPageForView(self):
        """Tests proper traversal of a page defined for a view."""

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public" />

            <browser:page name="index.html"
                for="zope.component.testfiles.views.IV"
                class="zope.browserpage.tests.test_page.CV"
                permission="zope.Public" />
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        view.publishTraverse(request, 'index.html')

    def testTraversalOfPageForViewWithPublishTraverse(self):
        """Tests proper traversal of a page defined for a view.

        This test is different from testTraversalOfPageForView in that it
        tests the behavior on a view that has a publishTraverse method --
        the implementation of the lookup is slightly different in such a
        case.
        """
        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.browserpage.tests.test_page.VT"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public" />

            <browser:page name="index.html"
                for="zope.component.testfiles.views.IV"
                class="zope.browserpage.tests.test_page.CV"
                permission="zope.Public" />
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        view.publishTraverse(request, 'index.html')

    def testProtectedPageViews(self):
        component.provideUtility(Permission('p', 'P'), IPermission, 'p')

        request = TestRequest()
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <include package="zope.security" file="meta.zcml" />

            <permission id="zope.TestPermission" title="Test permission" />

            <browser:pages
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.TestPermission"
                >

              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
            </browser:pages>
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        v = ProxyFactory(v)
        zope.security.management.getInteraction().add(request)
        self.assertRaises(Exception, v)
        v = component.getMultiAdapter((ob, request), name='action.html')
        v = ProxyFactory(v)
        self.assertRaises(Exception, v)

    def testProtectedNamedViewPageViews(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <include package="zope.security" file="meta.zcml" />

            <permission id="zope.TestPermission" title="Test permission" />

            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >

              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
            </browser:view>
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        self.assertEqual(view.browserDefault(request)[1], (u'index.html', ))

        v = view.publishTraverse(request, 'index.html')
        self.assertEqual(v(), 'V1 here')

    def testSkinnedPageView(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:pages
                for="*"
                class="zope.component.testfiles.views.V1"
                permission="zope.Public"
                >
              <browser:page name="index.html" attribute="index" />
            </browser:pages>

            <browser:pages
                for="*"
                class="zope.component.testfiles.views.V1"
                layer="
                  zope.browserpage.tests.test_page.ITestLayer"
                permission="zope.Public"
                >
              <browser:page name="index.html" attribute="action" />
            </browser:pages>
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        self.assertEqual(v(), 'V1 here')
        v = component.getMultiAdapter((ob, TestRequest(skin=ITestSkin)),
                                 name='index.html')
        self.assertEqual(v(), 'done')


    def test_template_page(self):
        path = os.path.join(tests_path, 'testfiles', 'test.pt')

        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='index.html'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:page
                name="index.html"
                template="%s"
                permission="zope.Public"
                for="zope.component.testfiles.views.IC" />
            ''' % path
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        self.assertEqual(v().strip(), '<html><body><p>test</p></body></html>')

    def test_page_menu_within_different_layers(self):
        path = os.path.join(tests_path, 'testfiles', 'test.pt')
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='index.html'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:menu
                id="test_menu"
                title="Test menu"
                interface="zope.browserpage.tests.test_page.ITestMenu"/>

            <browser:page
                name="index.html"
                permission="zope.Public"
                for="zope.component.testfiles.views.IC"
                template="%s"
                menu="test_menu" title="Index"/>

            <browser:page
                name="index.html"
                permission="zope.Public"
                for="zope.component.testfiles.views.IC"
                menu="test_menu" title="Index"
                template="%s"
                layer="zope.browserpage.tests.test_page.ITestLayer"/>
            ''' % (path, path)
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        self.assertEqual(v().strip(), '<html><body><p>test</p></body></html>')

    def testtemplateWClass(self):
        path = os.path.join(tests_path, 'testfiles', 'test2.pt')

        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='index.html'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:page
                name="index.html"
                template="%s"
                permission="zope.Public"
          class="zope.browserpage.tests.test_page.templateclass"
                for="zope.component.testfiles.views.IC" />
            ''' % path
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        self.assertEqual(v().strip(), '<html><body><p>42</p></body></html>')

    def testProtectedtemplate(self):

        path = os.path.join(tests_path, 'testfiles', 'test.pt')

        request = TestRequest()
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <include package="zope.security" file="meta.zcml" />

            <permission id="zope.TestPermission" title="Test permission" />

            <browser:page
                name="xxx.html"
                template="%s"
                permission="zope.TestPermission"
                for="zope.component.testfiles.views.IC" />
            ''' % path
            ))

        xmlconfig(StringIO(template %
            '''
            <browser:page
                name="index.html"
                template="%s"
                permission="zope.Public"
                for="zope.component.testfiles.views.IC" />
            ''' % path
            ))

        v = component.getMultiAdapter((ob, request), name='xxx.html')
        v = ProxyFactory(v)
        zope.security.management.getInteraction().add(request)
        self.assertRaises(Exception, v)

        v = component.getMultiAdapter((ob, request), name='index.html')
        v = ProxyFactory(v)
        self.assertEqual(v().strip(), '<html><body><p>test</p></body></html>')


    def testtemplateNoName(self):
        path = os.path.join(tests_path, 'testfiles', 'test.pt')
        self.assertRaises(
            ConfigurationError,
            xmlconfig,
            StringIO(template %
            '''
            <browser:page
                template="%s"
                for="zope.component.testfiles.views.IC"
                />
            ''' % path
            ))

    def testtemplateAndPage(self):
        path = os.path.join(tests_path, 'testfiles', 'test.pt')
        self.assertRaises(
            ConfigurationError,
            xmlconfig,
            StringIO(template %
            '''
            <browser:view
                name="index.html"
                template="%s"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >
              <browser:page name="foo.html" attribute="index" />
            </browser:view>
            ''' % path
            ))

    def testViewThatProvidesAnInterface(self):
        request = TestRequest()
        self.assertEqual(
            component.queryMultiAdapter((ob, request), IV, name='test'), None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                />
            '''
            ))

        v = component.queryMultiAdapter((ob, request), IV, name='test')
        self.assertEqual(v, None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                provides="zope.component.testfiles.views.IV"
                permission="zope.Public"
                />
            '''
            ))

        v = component.queryMultiAdapter((ob, request), IV, name='test')
        self.assert_(isinstance(v, V1))

    def testUnnamedViewThatProvidesAnInterface(self):
        request = TestRequest()
        self.assertEqual(component.queryMultiAdapter((ob, request), IV),
                         None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                />
            '''
            ))

        v = component.queryMultiAdapter((ob, request), IV)
        self.assertEqual(v, None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                provides="zope.component.testfiles.views.IV"
                permission="zope.Public"
                />
            '''
            ))

        v = component.queryMultiAdapter((ob, request), IV)

        self.assert_(isinstance(v, V1))


def test_suite():
    return unittest.makeSuite(Test)
