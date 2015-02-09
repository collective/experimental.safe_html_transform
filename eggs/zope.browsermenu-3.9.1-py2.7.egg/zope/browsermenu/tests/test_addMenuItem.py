#############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Test the addMenuItem directive

>>> context = Context()
>>> addMenuItem(context, class_=X, title="Add an X",
...             permission="zope.ManageContent")
>>> context
((('utility',
   <InterfaceClass zope.component.interfaces.IFactory>,
   'BrowserAdd__zope.browsermenu.tests.test_addMenuItem.X'),
  <function handler>,
  ('registerUtility',
   <Factory for <class 'zope.browsermenu.tests.test_addMenuItem.X'>>,
   <InterfaceClass zope.component.interfaces.IFactory>,
   'BrowserAdd__zope.browsermenu.tests.test_addMenuItem.X'),
  {'factory': None}),
 (None,
  <function provideInterface>,
  ('zope.component.interfaces.IFactory',
   <InterfaceClass zope.component.interfaces.IFactory>),
  {}),
 (('adapter',
   (<InterfaceClass zope.browser.interfaces.IAdding>,
    <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
   <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
   'Add an X'),
  <function handler>,
  ('registerAdapter',
   <zope.browsermenu.metaconfigure.MenuItemFactory object>,
   (<InterfaceClass zope.browser.interfaces.IAdding>,
    <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
   <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
   'Add an X',
   ''),
  {}),
 (None,
  <function provideInterface>,
  ('',
   <InterfaceClass zope.browsermenu.interfaces.AddMenu>),
  {}),
 (None,
  <function provideInterface>,
  ('', <InterfaceClass zope.browser.interfaces.IAdding>),
  {}),
 (None,
  <function provideInterface>,
  ('',
   <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
  {}))

$Id: test_addMenuItem.py 111004 2010-04-16 20:13:36Z tseaver $
"""

import unittest
from doctest import DocTestSuite
import re
import pprint
import cStringIO
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.browsermenu.metaconfigure import addMenuItem

atre = re.compile(' at [0-9a-fA-Fx]+')

class IX(Interface):
    pass

class X(object):
    pass

class ILayerStub(IBrowserRequest):
    pass

class MenuStub(object):
    pass


class Context(object):
    actions = ()
    info = ''

    def action(self, discriminator, callable, args=(), kw={}, order=0):
        self.actions += ((discriminator, callable, args, kw), )

    def __repr__(self):
        stream = cStringIO.StringIO()
        pprinter = pprint.PrettyPrinter(stream=stream, width=60)
        pprinter.pprint(self.actions)
        r = stream.getvalue()
        return (''.join(atre.split(r))).strip()


def test_w_factory():
    """
    >>> context = Context()
    >>> addMenuItem(context, factory="x.y.z", title="Add an X",
    ...             permission="zope.ManageContent", description="blah blah",
    ...             filter="context/foo")
    >>> context
    ((('adapter',
       (<InterfaceClass zope.browser.interfaces.IAdding>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X'),
      <function handler>,
      ('registerAdapter',
       <zope.browsermenu.metaconfigure.MenuItemFactory object>,
       (<InterfaceClass zope.browser.interfaces.IAdding>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X',
       ''),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>),
      {}),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.browser.interfaces.IAdding>),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
      {}))
    """

def test_w_factory_and_view():
    """
    >>> context = Context()
    >>> addMenuItem(context, factory="x.y.z", title="Add an X",
    ...             permission="zope.ManageContent", description="blah blah",
    ...             filter="context/foo", view="AddX")
    >>> context
    ((None,
      <function _checkViewFor>,
      (<InterfaceClass zope.browser.interfaces.IAdding>,
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>,
       'AddX'),
      {}),
     (('adapter',
       (<InterfaceClass zope.browser.interfaces.IAdding>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X'),
      <function handler>,
      ('registerAdapter',
       <zope.browsermenu.metaconfigure.MenuItemFactory object>,
       (<InterfaceClass zope.browser.interfaces.IAdding>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X',
       ''),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>),
      {}),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.browser.interfaces.IAdding>),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
      {}))
    """

def test_w_factory_class_view():
    """
    >>> context = Context()
    >>> addMenuItem(context, class_=X, title="Add an X",
    ...             permission="zope.ManageContent", description="blah blah",
    ...             filter="context/foo", view="AddX")
    >>> import pprint
    >>> context
    ((('utility',
       <InterfaceClass zope.component.interfaces.IFactory>,
       'BrowserAdd__zope.browsermenu.tests.test_addMenuItem.X'),
      <function handler>,
      ('registerUtility',
       <Factory for <class 'zope.browsermenu.tests.test_addMenuItem.X'>>,
       <InterfaceClass zope.component.interfaces.IFactory>,
       'BrowserAdd__zope.browsermenu.tests.test_addMenuItem.X'),
      {'factory': None}),
     (None,
      <function provideInterface>,
      ('zope.component.interfaces.IFactory',
       <InterfaceClass zope.component.interfaces.IFactory>),
      {}),
     (None,
      <function _checkViewFor>,
      (<InterfaceClass zope.browser.interfaces.IAdding>,
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>,
       'AddX'),
      {}),
     (('adapter',
       (<InterfaceClass zope.browser.interfaces.IAdding>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X'),
      <function handler>,
      ('registerAdapter',
       <zope.browsermenu.metaconfigure.MenuItemFactory object>,
       (<InterfaceClass zope.browser.interfaces.IAdding>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X',
       ''),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>),
      {}),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.browser.interfaces.IAdding>),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
      {}))
    """

def test_w_for_factory():
    """
    >>> context = Context()
    >>> addMenuItem(context, for_=IX, factory="x.y.z", title="Add an X",
    ...             permission="zope.ManageContent", description="blah blah",
    ...             filter="context/foo")
    >>> context
    ((None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.tests.test_addMenuItem.IX>),
      {}),
     (('adapter',
       (<InterfaceClass zope.browsermenu.tests.test_addMenuItem.IX>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X'),
      <function handler>,
      ('registerAdapter',
       <zope.browsermenu.metaconfigure.MenuItemFactory object>,
       (<InterfaceClass zope.browsermenu.tests.test_addMenuItem.IX>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X',
       ''),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.tests.test_addMenuItem.IX>),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
      {}))
    """

def test_w_factory_layer():
    """
    >>> context = Context()
    >>> addMenuItem(context, factory="x.y.z", title="Add an X", layer=ILayerStub,
    ...             permission="zope.ManageContent", description="blah blah",
    ...             filter="context/foo")
    >>> context
    ((('adapter',
       (<InterfaceClass zope.browser.interfaces.IAdding>,
        <InterfaceClass zope.browsermenu.tests.test_addMenuItem.ILayerStub>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X'),
      <function handler>,
      ('registerAdapter',
       <zope.browsermenu.metaconfigure.MenuItemFactory object>,
       (<InterfaceClass zope.browser.interfaces.IAdding>,
        <InterfaceClass zope.browsermenu.tests.test_addMenuItem.ILayerStub>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X',
       ''),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>),
      {}),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.browser.interfaces.IAdding>),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.tests.test_addMenuItem.ILayerStub>),
      {}))
    """

def test_w_for_menu_factory():
    """
    >>> context = Context()
    >>> addMenuItem(context, for_=IX, menu=MenuStub, factory="x.y.z", title="Add an X",
    ...             permission="zope.ManageContent", description="blah blah",
    ...             filter="context/foo")
    >>> context
    ((None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.tests.test_addMenuItem.IX>),
      {}),
     (('adapter',
       (<InterfaceClass zope.browsermenu.tests.test_addMenuItem.IX>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <class 'zope.browsermenu.tests.test_addMenuItem.MenuStub'>,
       'Add an X'),
      <function handler>,
      ('registerAdapter',
       <zope.browsermenu.metaconfigure.MenuItemFactory object>,
       (<InterfaceClass zope.browsermenu.tests.test_addMenuItem.IX>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <class 'zope.browsermenu.tests.test_addMenuItem.MenuStub'>,
       'Add an X',
       ''),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <class 'zope.browsermenu.tests.test_addMenuItem.MenuStub'>),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.tests.test_addMenuItem.IX>),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
      {}))
    """

def test_w_factory_icon_extra_order():
    """
    >>> context = Context()
    >>> addMenuItem(context, factory="x.y.z", title="Add an X",
    ...             permission="zope.ManageContent", description="blah blah",
    ...             filter="context/foo", icon=u'/@@/icon.png', extra='Extra',
    ...             order=99)
    >>> context
    ((('adapter',
       (<InterfaceClass zope.browser.interfaces.IAdding>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X'),
      <function handler>,
      ('registerAdapter',
       <zope.browsermenu.metaconfigure.MenuItemFactory object>,
       (<InterfaceClass zope.browser.interfaces.IAdding>,
        <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>,
       'Add an X',
       ''),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.browsermenu.interfaces.AddMenu>),
      {}),
     (None,
      <function provideInterface>,
      ('', <InterfaceClass zope.browser.interfaces.IAdding>),
      {}),
     (None,
      <function provideInterface>,
      ('',
       <InterfaceClass zope.publisher.interfaces.browser.IDefaultBrowserLayer>),
      {}))
    """

from zope.configuration.xmlconfig import XMLConfig

import zope.browsermenu
import zope.component
from zope.testing import cleanup

class TestAddMenuItem(cleanup.CleanUp, unittest.TestCase):

    def setUp(self):
        super(TestAddMenuItem, self).setUp()
        XMLConfig('meta.zcml', zope.component)()
        XMLConfig('meta.zcml', zope.browsermenu)()

    def test_addMenuItemDirectives(self):
        XMLConfig('tests/addmenuitems.zcml', zope.browsermenu)()

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        unittest.makeSuite(TestAddMenuItem),
        ))

if __name__ == '__main__':
    unittest.main()
