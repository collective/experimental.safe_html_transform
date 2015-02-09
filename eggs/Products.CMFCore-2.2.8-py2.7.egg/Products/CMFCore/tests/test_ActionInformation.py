##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for ActionInformation module. """

import unittest
import Testing

from OFS.Folder import manage_addFolder
from Products.PythonScripts.PythonScript import manage_addPythonScript
from zope.interface.verify import verifyClass

from Products.CMFCore.Expression import createExprContext
from Products.CMFCore.Expression import Expression
from Products.CMFCore.testing import FunctionalZCMLLayer
from Products.CMFCore.tests.base.dummy import DummyContent
from Products.CMFCore.tests.base.dummy import DummySite
from Products.CMFCore.tests.base.dummy import DummyTool as DummyMembershipTool
from Products.CMFCore.tests.base.testcase import SecurityTest
from Products.CMFCore.tests.base.testcase import TransactionalTest


class ActionCategoryTests(unittest.TestCase):

    def _makeOne(self, *args, **kw):
        from Products.CMFCore.ActionInformation import ActionCategory

        return ActionCategory(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCore.ActionInformation import ActionCategory
        from Products.CMFCore.interfaces import IActionCategory

        verifyClass(IActionCategory, ActionCategory)

    def test_listActions(self):
        from Products.CMFCore.ActionInformation import Action

        ac = self._makeOne('foo')
        self.assertEqual( ac.listActions(), () )

        baz = Action('baz')
        ac._setObject('baz', baz)
        self.assertEqual( ac.listActions(), (baz,) )


class ActionTests(unittest.TestCase):

    def _makeOne(self, *args, **kw):
        from Products.CMFCore.ActionInformation import Action

        return Action(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCore.ActionInformation import Action
        from Products.CMFCore.interfaces import IAction

        verifyClass(IAction, Action)

    def test_getInfoData_empty(self):
        WANTED = ( {'available': True, 'category': '', 'description': '',
                    'id': 'foo', 'icon': '', 'permissions': (), 'title': '',
                    'url': '', 'visible': True, 'link_target': None}, [] )
        a = self._makeOne('foo')
        self.assertEqual( a.getInfoData(), WANTED )

    def test_getInfoData_normal(self):
        a = self._makeOne('foo',
                          title='Foo Title',
                          description='Foo description.',
                          url_expr='string:${object_url}/foo_url',
                          icon_expr='string:foo_icon',
                          available_expr='',
                          permissions=('View',),
                          visible=False,
                          link_target='_top')
        WANTED = ( {'available': True, 'category': '',
                    'description': 'Foo description.',
                    'id': 'foo', 'icon': a.icon_expr_object,
                    'permissions': ('View',), 'title': 'Foo Title',
                    'url': a.url_expr_object, 'visible': False,
                    'link_target': a.link_target },
                   ['url', 'icon'] )
        self.assertEqual( a.getInfoData(), WANTED )

    def test_manage_propertiesForm_allows_adding(self):
        from OFS.SimpleItem import SimpleItem
        def _header(*args, **kw):
            return 'HEADER'
        def _footer(*args, **kw):
            return 'HEADER'
        container = SimpleItem()

        container.REQUEST = request = DummyRequest()
        request.set('manage_page_header', _header)
        request.set('manage_page_footer', _footer)
        request.set('BASEPATH1', '/one/two')
        setattr(request, 'URL1', '/one/two')
        request._steps = ['one', 'two']

        prd = {'ac_permissions': ('a', 'b')}
        container._getProductRegistryData = prd.get

        a = self._makeOne('extensible').__of__(container)
        form_html = a.manage_propertiesForm(request)

        self.assertTrue('value=" Add "' in form_html)

    def test_clearExprObjects(self):
        """When a *_expr property is set, a *_expr_object attribute is
        also set which should also be cleared when the *_expr is
        cleared."""
        a = self._makeOne('foo',
                          title='Foo Title',
                          description='Foo description.',
                          url_expr='string:${object_url}/foo_url',
                          icon_expr='string:foo_icon',
                          available_expr='',
                          permissions=('View',),
                          visible=False,
                          link_target='_top')
        self.assertTrue(hasattr(a, 'icon_expr_object'))
        self.assertTrue(hasattr(a, 'url_expr_object'))
        self.assertFalse(hasattr(a, 'available_expr_object'))
        a.manage_changeProperties(
            icon_expr='', url_expr='', available_expr='')
        self.assertFalse(hasattr(a, 'icon_expr_object'))
        self.assertFalse(hasattr(a, 'url_expr_object'))
        self.assertFalse(hasattr(a, 'available_expr_object'))


class DummyRequest:
    def __init__(self):
        self._data = {}
    def set(self, k, v):
        self._data[k] = v
    def get(self, k, default):
        return self._data.get(k, default)
    def __getitem__(self, k):
        return self._data[k]
    def __len__(self):
        return len(self._data)

class ActionInfoTests(unittest.TestCase):

    def _makeOne(self, *args, **kw):
        from Products.CMFCore.ActionInformation import ActionInfo

        return ActionInfo(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCore.ActionInformation import ActionInfo
        from Products.CMFCore.interfaces import IActionInfo

        verifyClass(IActionInfo, ActionInfo)

    def test_create_from_Action(self):
        from Products.CMFCore.ActionInformation import Action

        WANTED = {'allowed': True, 'available': True, 'category': '',
                  'description': '', 'icon': '', 'id': 'foo', 'title': '',
                  'url': '', 'visible': True, 'link_target': None}

        action = Action(id='foo')
        ec = None
        ai = self._makeOne(action, ec)

        self.assertEqual( ai['id'], WANTED['id'] )
        self.assertEqual( ai['title'], WANTED['title'] )
        self.assertEqual( ai['description'], WANTED['description'] )
        self.assertEqual( ai['url'], WANTED['url'] )
        self.assertEqual( ai['category'], WANTED['category'] )
        self.assertEqual( ai['visible'], WANTED['visible'] )
        self.assertEqual( ai['available'], WANTED['available'] )
        self.assertEqual( ai['allowed'], WANTED['allowed'] )
        self.assertEqual( ai, WANTED )

    def test_create_from_ActionInformation(self):
        from Products.CMFCore.ActionInformation import ActionInformation

        WANTED = {'allowed': True, 'available': True, 'category': 'object',
                  'description': '', 'id': 'foo', 'title': 'foo', 'url': '',
                  'visible': True, 'icon': '', 'link_target': None}

        action = ActionInformation(id='foo')
        ec = None
        ai = self._makeOne(action, ec)

        self.assertEqual( ai['id'], WANTED['id'] )
        self.assertEqual( ai['title'], WANTED['title'] )
        self.assertEqual( ai['description'], WANTED['description'] )
        self.assertEqual( ai['url'], WANTED['url'] )
        self.assertEqual( ai['icon'], WANTED['icon'] )
        self.assertEqual( ai['category'], WANTED['category'] )
        self.assertEqual( ai['visible'], WANTED['visible'] )
        self.assertEqual( ai['available'], WANTED['available'] )
        self.assertEqual( ai['allowed'], WANTED['allowed'] )
        self.assertEqual( ai, WANTED )

    def test_create_from_dict(self):
        WANTED = {'allowed': True, 'available': True, 'category': 'object',
                  'id': 'foo', 'title': 'foo', 'url': '', 'visible': True,
                  'icon': '' , 'link_target': None}

        action = {'name': 'foo', 'url': ''}
        ec = None
        ai = self._makeOne(action, ec)

        self.assertEqual( ai['id'], WANTED['id'] )
        self.assertEqual( ai['title'], WANTED['title'] )
        self.assertEqual( ai['url'], WANTED['url'] )
        self.assertEqual( ai['icon'], WANTED['icon'] )
        self.assertEqual( ai['category'], WANTED['category'] )
        self.assertEqual( ai['visible'], WANTED['visible'] )
        self.assertEqual( ai['available'], WANTED['available'] )
        self.assertEqual( ai['allowed'], WANTED['allowed'] )
        self.assertEqual( ai, WANTED )


class ActionInfoSecurityTests(SecurityTest):

    def setUp(self):
        SecurityTest.setUp(self)
        self.site = DummySite('site').__of__(self.root)
        self.site._setObject( 'portal_membership', DummyMembershipTool() )

    def _makeOne(self, *args, **kw):
        from Products.CMFCore.ActionInformation import ActionInfo

        return ActionInfo(*args, **kw)

    def test_create_from_dict(self):
        WANTED = {'allowed': True, 'available': True, 'category': 'object',
                  'id': 'foo', 'title': 'foo', 'url': '', 'visible': True,
                  'icon': '', 'link_target': None}

        action = {'name': 'foo', 'url': '', 'permissions': ('View',)}
        ec = createExprContext(self.site, self.site, None)
        ai = self._makeOne(action, ec)

        self.assertEqual( ai['id'], WANTED['id'] )
        self.assertEqual( ai['title'], WANTED['title'] )
        self.assertEqual( ai['url'], WANTED['url'] )
        self.assertEqual( ai['icon'], WANTED['icon'] )
        self.assertEqual( ai['category'], WANTED['category'] )
        self.assertEqual( ai['visible'], WANTED['visible'] )
        self.assertEqual( ai['available'], WANTED['available'] )
        self.assertEqual( ai['allowed'], WANTED['allowed'] )
        self.assertEqual( ai, WANTED )

    def test_category_object(self):
        # Permissions for action category 'object*' should be
        # evaluated in object context.
        manage_addFolder(self.site, 'actions_dummy')
        self.object = self.site.actions_dummy
        self.object.manage_permission('View', [], acquire=0)

        WANTED = {'allowed': False, 'category': 'object'}

        action = {'name': 'foo', 'url': '', 'permissions': ('View',)}
        ec = createExprContext(self.site, self.site, self.object)
        ai = self._makeOne(action, ec)

        self.assertEqual( ai['category'], WANTED['category'] )
        self.assertEqual( ai['allowed'], WANTED['allowed'] )

    def test_category_folder(self):
        # Permissions for action category 'folder*' should be
        # evaluated in folder context.
        manage_addFolder(self.site, 'actions_dummy')
        self.folder = self.site.actions_dummy
        self.folder.manage_permission('View', [], acquire=0)

        WANTED = {'allowed': False, 'category': 'folder'}

        action = {'name': 'foo', 'url': '', 'permissions': ('View',)}
        ec = createExprContext(self.folder, self.site, None)
        ai = self._makeOne(action, ec)
        ai['category'] = 'folder' # pfff

        self.assertEqual( ai['category'], WANTED['category'] )
        self.assertEqual( ai['allowed'], WANTED['allowed'] )

    def test_category_workflow(self):
        # Permissions for action category 'workflow*' should be
        # evaluated in object context.
        manage_addFolder(self.site, 'actions_dummy')
        self.object = self.site.actions_dummy
        self.object.manage_permission('View', [], acquire=0)

        WANTED = {'allowed': False, 'category': 'workflow'}

        action = {'name': 'foo', 'url': '', 'permissions': ('View',)}
        ec = createExprContext(self.site, self.site, self.object)
        ai = self._makeOne(action, ec)
        ai['category'] = 'workflow' # pfff

        self.assertEqual( ai['category'], WANTED['category'] )
        self.assertEqual( ai['allowed'], WANTED['allowed'] )

    def test_category_document(self):
        # Permissions for action category 'document*' should be
        # evaluated in object context (not in portal context).
        manage_addFolder(self.site, 'actions_dummy')
        self.object = self.site.actions_dummy
        self.object.manage_permission('View', [], acquire=0)

        WANTED = {'allowed': False, 'category': 'document'}

        action = {'name': 'foo', 'url': '', 'permissions': ('View',)}
        ec = createExprContext(self.site, self.site, self.object)
        ai = self._makeOne(action, ec)
        ai['category'] = 'document' # pfff

        self.assertEqual( ai['category'], WANTED['category'] )
        self.assertEqual( ai['allowed'], WANTED['allowed'] )

    def test_copy(self):
        action = {'name': 'foo', 'url': '', 'permissions': ('View',)}
        ec = createExprContext(self.site, self.site, None)
        ai = self._makeOne(action, ec)
        ai2 = ai.copy()

        self.assertEqual( ai._lazy_keys, ['allowed'] )
        self.assertEqual( ai2._lazy_keys, ['allowed'] )
        self.assertFalse( ai2._lazy_keys is ai._lazy_keys )
        self.assertEqual( ai['allowed'], True )
        self.assertEqual( ai2['allowed'], True )


class ActionInformationTests(TransactionalTest):

    layer = FunctionalZCMLLayer

    def setUp(self):
        TransactionalTest.setUp(self)

        root = self.root
        root._setObject('portal', DummyContent('portal', 'url_portal'))
        portal = self.portal = root.portal
        portal.portal_membership = DummyMembershipTool()
        self.folder = DummyContent('foo', 'url_foo')
        self.object = DummyContent('bar', 'url_bar')

    def _makeOne(self, *args, **kw):
        from Products.CMFCore.ActionInformation import ActionInformation

        return ActionInformation(*args, **kw)

    def test_interfaces(self):
        from Products.CMFCore.ActionInformation import ActionInformation
        from Products.CMFCore.interfaces import IAction

        verifyClass(IAction, ActionInformation)

    def test_basic_construction(self):
        ai = self._makeOne(id='view')

        self.assertEqual(ai.getId(), 'view')
        self.assertEqual(ai.Title(), 'view')
        self.assertEqual(ai.Description(), '')
        self.assertEqual(ai.getCondition(), '')
        self.assertEqual(ai.getActionExpression(), '')
        self.assertEqual(ai.getVisibility(), 1)
        self.assertEqual(ai.getCategory(), 'object')
        self.assertEqual(ai.getPermissions(), ())

    def test_editing(self):
        ai = self._makeOne(id='view', category='folder')
        ai.edit(id='new_id', title='blah')

        self.assertEqual(ai.getId(), 'new_id')
        self.assertEqual(ai.Title(), 'blah')
        self.assertEqual(ai.Description(), '')
        self.assertEqual(ai.getCondition(), '')
        self.assertEqual(ai.getActionExpression(), '')
        self.assertEqual(ai.getVisibility(), 1)
        self.assertEqual(ai.getCategory(), 'folder')
        self.assertEqual(ai.getPermissions(), ())

    def test_setActionExpression_with_string_prefix(self):
        from Products.CMFCore.Expression import Expression
        ai = self._makeOne(id='view', category='folder')
        ai.setActionExpression('string:blah')
        self.assertTrue(isinstance(ai.action,Expression))
        self.assertEqual(ai.getActionExpression(), 'string:blah')

    def test_construction_with_Expressions(self):
        ai = self._makeOne( id='view',
                            title='View',
                            action=Expression(text='view'),
                            condition=Expression(text='member'),
                            category='global',
                            visible=False )

        self.assertEqual(ai.getId(), 'view')
        self.assertEqual(ai.Title(), 'View')
        self.assertEqual(ai.Description(), '')
        self.assertEqual(ai.getCondition(), 'member')
        self.assertEqual(ai.getActionExpression(), 'string:${object_url}/view')
        self.assertEqual(ai.getVisibility(), 0)
        self.assertEqual(ai.getCategory(), 'global')
        self.assertEqual(ai.getPermissions(), ())

    def test_Condition(self):
        portal = self.portal
        folder = self.folder
        object = self.object
        ai = self._makeOne( id='view',
                            title='View',
                            action=Expression(text='view'),
                            condition=Expression(text='member'),
                            category='global',
                            visible=True )
        ec = createExprContext(folder, portal, object)

        self.assertFalse(ai.testCondition(ec))

    def test_Condition_PathExpression(self):
        portal = self.portal
        folder = self.folder
        object = self.object
        manage_addPythonScript(self.root, 'test_script')
        script = self.root.test_script
        script.ZPythonScript_edit('', 'return context.getId()')
        ai = self._makeOne( id='view',
                            title='View',
                            action=Expression(text='view'),
                            condition=Expression(text='portal/test_script'),
                            category='global',
                            visible=True )
        ec = createExprContext(folder, portal, object)

        self.assertTrue(ai.testCondition(ec))

    def test_getInfoData_empty(self):
        WANTED = ( {'available': True, 'category': 'object',
                    'description': '', 'id': 'foo', 'permissions': (),
                    'title': 'foo', 'url': '', 'visible': True, 'icon': '',
                    'link_target': None},[])
        a = self._makeOne('foo')
        self.assertEqual( a.getInfoData(), WANTED )

    def test_getInfoData_normal(self):
        a = self._makeOne('foo',
                          title='Foo Title',
                          description='Foo description.',
                          action='string:${object_url}/foo_url',
                          icon_expr='string:${object_url}/icon.gif',
                          condition='',
                          permissions=('View',),
                          visible=False,
                          link_target='_top')
        WANTED = ( {'available': True, 'category': 'object',
                    'description': 'Foo description.', 'id': 'foo',
                    'permissions': ('View',), 'title': 'Foo Title',
                    'url': a._getActionObject(), 'visible': False,
                    'icon': a._getIconExpressionObject(), 
                    'link_target': a.link_target },
                   ['url', 'icon'] )
        self.assertEqual( a.getInfoData(), WANTED )


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ActionCategoryTests),
        unittest.makeSuite(ActionTests),
        unittest.makeSuite(ActionInfoTests),
        unittest.makeSuite(ActionInfoSecurityTests),
        unittest.makeSuite(ActionInformationTests),
        ))

if __name__ == '__main__':
    from Products.CMFCore.testing import run
    run(test_suite())
