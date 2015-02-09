##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Test Products.CMFDefault.browser.ursa """
import unittest
from zope.component.testing import PlacelessSetup

class UrsineGlobalsTests(unittest.TestCase, PlacelessSetup):

    def setUp(self):
        PlacelessSetup.setUp(self)

    def tearDown(self):
        PlacelessSetup.tearDown(self)

    def _getTargetClass(self):
        from Products.CMFDefault.browser.ursa import UrsineGlobals
        return UrsineGlobals

    def _makeOne(self, context=None, request=None):
        if context is None:
            context = self._makeContext()
        if request is None:
            request = DummyRequest()
        return self._getTargetClass()(context, request)

    def _makeContext(self):
        from zope.component import getSiteManager
        from Products.CMFCore.interfaces import IPropertiesTool
        context = DummyContext()
        tool = context.portal_properties = DummyPropertiesTool()
        sm = getSiteManager()
        sm.registerUtility(tool, IPropertiesTool)
        return context

    def test_ctor_wo_def_charset_doesnt_set_content_type(self):
        context = self._makeContext()
        request = DummyRequest()
        response = request.RESPONSE
        view = self._makeOne(context, request)
        self.assertEqual(len(response._set_headers), 0)

    def test_ctor_w_resp_charset_doesnt_set_content_type(self):
        context = self._makeContext()
        request = DummyRequest()
        response = request.RESPONSE
        response._orig_headers['content-type'] = 'text/html; charset=UTF-8'
        view = self._makeOne(context, request)
        self.assertEqual(len(response._set_headers), 0)

    def test_ctor_w_resp_charset_w_def_charset_doesnt_override_charset(self):
        context = self._makeContext()
        context.portal_properties.default_charset = 'latin1'
        request = DummyRequest()
        response = request.RESPONSE
        response._orig_headers['content-type'] = 'text/html; charset=UTF-8'
        view = self._makeOne(context, request)
        self.assertEqual(len(response._set_headers), 0)

    def test_ctor_wo_resp_charst_w_def_charset_sets_charset(self):
        context = self._makeContext()
        context.portal_properties.default_charset = 'latin1'
        request = DummyRequest()
        response = request.RESPONSE
        response._orig_headers['content-type'] = 'text/html'
        view = self._makeOne(context, request)
        self.assertEqual(len(response._set_headers), 1)
        self.assertEqual(response._set_headers[0],
                         ('content-type', 'text/html; charset=latin1'))

    def test_ptool(self):
        view = self._makeOne()
        tool = view.context.portal_properties
        self.failUnless(view.ptool is tool)

    def test_utool(self):
        view = self._makeOne()
        tool = view.context.portal_url = DummyURLTool()
        self.failUnless(view.utool is tool)

    def test_mtool(self):
        view = self._makeOne()
        tool = view.context.portal_membership = DummyMembershipTool()
        self.failUnless(view.mtool is tool)

    def test_atool(self):
        view = self._makeOne()
        tool = view.context.portal_actions = DummyActionsTool()
        self.failUnless(view.atool is tool)

    def test_wtool(self):
        view = self._makeOne()
        tool = view.context.portal_workflow = DummyWorkflowTool()
        self.failUnless(view.wtool is tool)

    def test_portal_object(self):
        view = self._makeOne()
        tool = view.context.portal_url = DummyURLTool()
        portal = DummyContext()
        tool.getPortalObject = lambda: portal
        self.failUnless(view.portal_object is portal)

    def test_portal_url(self):
        view = self._makeOne()
        tool = view.context.portal_url = DummyURLTool()
        tool.__call__ = lambda: 'http://example.com/'
        self.assertEqual(view.portal_url, 'http://example.com/')

    def test_portal_title(self):
        view = self._makeOne()
        tool = view.context.portal_url = DummyURLTool()
        portal = DummyContext()
        portal.Title = lambda: 'TITLE'
        tool.getPortalObject = lambda: portal
        self.assertEqual(view.portal_title, 'TITLE')

    def test_object_title(self):
        view = self._makeOne()
        view.context.Title = lambda: 'TITLE'
        self.assertEqual(view.object_title, 'TITLE')

    def test_object_description(self):
        view = self._makeOne()
        view.context.Title = lambda: 'TITLE'
        self.assertEqual(view.object_title, 'TITLE')

    def test_trunc_id(self):
        view = self._makeOne()
        view.context.getId = lambda: 'ID'
        self.assertEqual(view.trunc_id, 'ID')

    def test_trunc_id_w_long_id(self):
        view = self._makeOne()
        view.context.getId = lambda: 'X' * 20
        self.assertEqual(view.trunc_id, 'X' * 15 + '...')

    def test_icon_wo_getIconURL_w_icon(self):
        view = self._makeOne()
        view.context.getIconURL = lambda: 'ICON'
        view.context.icon = 'ICON2'
        self.assertEqual(view.icon, 'ICON')

    def test_icon_wo_getIconURL_w_icon(self):
        view = self._makeOne()
        view.context.icon = 'ICON'
        self.assertEqual(view.icon, 'ICON')

    def test_icon_wo_getIconURL_wo_icon(self):
        view = self._makeOne()
        self.assertEqual(view.icon, '')

    def test_typename(self):
        view = self._makeOne()
        view.context.getPortalTypeName = lambda: 'TYPENAME'
        self.assertEqual(view.typename, 'TYPENAME')

    def test_wf_state(self):
        view = self._makeOne()
        view.context.portal_workflow = DummyWorkflowTool()
        self.assertEqual(view.wf_state, 'DUMMY')

    def test_page_title_wo_match(self):
        view = self._makeOne()
        view.context.Title = lambda: 'CONTEXT'
        tool = view.context.portal_url = DummyURLTool()
        portal = DummyContext()
        portal.Title = lambda: 'SITE'
        tool.getPortalObject = lambda: portal
        self.assertEqual(view.page_title, 'SITE: CONTEXT')

    def test_page_title_w_match(self):
        view = self._makeOne()
        view.context.Title = lambda: 'MATCH'
        tool = view.context.portal_url = DummyURLTool()
        portal = DummyContext()
        portal.Title = lambda: 'MATCH'
        tool.getPortalObject = lambda: portal
        self.assertEqual(view.page_title, 'MATCH')

    def test_breadcrumbs_at_root(self):
        PATHS_TO_CONTEXTS = []
        site = DummySite(PATHS_TO_CONTEXTS)
        ptool = site.portal_properties = DummyPropertiesTool()
        ptool.title = lambda: 'SITE'
        utool = site.portal_url = DummyURLTool(site, PATHS_TO_CONTEXTS)
        utool.__call__ = lambda: 'http://example.com/'
        view = self._makeOne(context=site)
        crumbs = view.breadcrumbs
        self.assertEqual(len(crumbs), 1)
        self.assertEqual(crumbs[0]['id'], 'root')
        self.assertEqual(crumbs[0]['title'], 'SITE')
        self.assertEqual(crumbs[0]['url'], 'http://example.com/')

    def test_breadcrumbs_not_root(self):
        context = DummyContext()
        context.Title = lambda: 'CONTEXT'
        context.absolute_url = lambda: 'http://example.com/parent/child'
        parent = DummyContext()
        parent.Title = lambda: 'PARENT'
        parent.absolute_url = lambda: 'http://example.com/parent'
        PATHS_TO_CONTEXTS = [(('parent',), parent),
                             (('parent', 'child'), context),
                            ]
        site = DummySite(PATHS_TO_CONTEXTS)
        ptool = context.portal_properties = DummyPropertiesTool()
        ptool.title = lambda: 'SITE'
        utool = context.portal_url = DummyURLTool(site, PATHS_TO_CONTEXTS)
        utool.__call__ = lambda: 'http://example.com/'

        view = self._makeOne(context=context)

        crumbs = view.breadcrumbs

        self.assertEqual(len(crumbs), 3)
        self.assertEqual(crumbs[0]['id'], 'root')
        self.assertEqual(crumbs[0]['title'], 'SITE')
        self.assertEqual(crumbs[0]['url'], 'http://example.com/')
        self.assertEqual(crumbs[1]['id'], 'parent')
        self.assertEqual(crumbs[1]['title'], 'PARENT')
        self.assertEqual(crumbs[1]['url'], 'http://example.com/parent')
        self.assertEqual(crumbs[2]['id'], 'child')
        self.assertEqual(crumbs[2]['title'], 'CONTEXT')
        self.assertEqual(crumbs[2]['url'], 'http://example.com/parent/child')

    def test_member(self):
        view = self._makeOne()
        tool = view.context.portal_membership = DummyMembershipTool()
        member = DummyUser()
        tool.getAuthenticatedMember = lambda: member
        self.failUnless(view.member is member)

    def test_membersfolder(self):
        view = self._makeOne()
        tool = view.context.portal_membership = DummyMembershipTool()
        membersfolder = object()
        tool.getMembersFolder = lambda: membersfolder
        self.failUnless(view.membersfolder is membersfolder)

    def test_isAnon_tool_returns_True(self):
        view = self._makeOne()
        tool = view.context.portal_membership = DummyMembershipTool()
        tool.isAnonymousUser = lambda: True
        self.failUnless(view.isAnon)

    def test_isAnon_tool_returns_False(self):
        view = self._makeOne()
        tool = view.context.portal_membership = DummyMembershipTool()
        tool.isAnonymousUser = lambda: False
        self.failIf(view.isAnon)

    def test_uname_anonymous(self):
        view = self._makeOne()
        tool = view.context.portal_membership = DummyMembershipTool()
        tool.isAnonymousUser = lambda: True
        self.assertEqual(view.uname, 'Guest')

    def test_uname_not_anonymous(self):
        view = self._makeOne()
        tool = view.context.portal_membership = DummyMembershipTool()
        tool.isAnonymousUser = lambda: False
        member = DummyUser()
        member.getUserName = lambda: 'luser'
        tool.getAuthenticatedMember = lambda: member
        self.assertEqual(view.uname, 'luser')

    def test_status_message_missing(self):
        view = self._makeOne()
        view.request.form = {}
        self.assertEqual(view.status_message, None)

    def test_status_message_missing(self):
        view = self._makeOne()
        view.request.form = {'portal_status_message': 'FOO'}
        self.assertEqual(view.status_message, 'FOO')

    def test_actions(self):
        ACTIONS = {'global': [],
                   'user': [],
                   'object': [],
                   'folder': [],
                   'workflow': [],
                  }
        view = self._makeOne()
        tool = view.context.portal_actions = DummyActionsTool(ACTIONS)
        self.assertEqual(view.actions, ACTIONS)

    def test_global_actions(self):
        ACTIONS = {'global': [DummyAction('a'), DummyAction('b')],
                   'user': [],
                   'object': [],
                   'folder': [],
                   'workflow': [],
                  }
        view = self._makeOne()
        tool = view.context.portal_actions = DummyActionsTool(ACTIONS)
        self.assertEqual(view.global_actions, ACTIONS['global'])

    def test_user_actions(self):
        ACTIONS = {'global': [],
                   'user': [DummyAction('a'), DummyAction('b')],
                   'object': [],
                   'folder': [],
                   'workflow': [],
                  }
        view = self._makeOne()
        tool = view.context.portal_actions = DummyActionsTool(ACTIONS)
        self.assertEqual(view.user_actions, ACTIONS['user'])

    def test_object_actions(self):
        ACTIONS = {'global': [],
                   'user': [],
                   'object': [DummyAction('a'), DummyAction('b')],
                   'folder': [],
                   'workflow': [],
                  }
        view = self._makeOne()
        tool = view.context.portal_actions = DummyActionsTool(ACTIONS)
        self.assertEqual(view.object_actions, ACTIONS['object'])

    def test_folder_actions(self):
        ACTIONS = {'global': [],
                   'user': [],
                   'object': [],
                   'folder': [DummyAction('a'), DummyAction('b')],
                   'workflow': [],
                  }
        view = self._makeOne()
        tool = view.context.portal_actions = DummyActionsTool(ACTIONS)
        self.assertEqual(view.folder_actions, ACTIONS['folder'])

    def test_workflow_actions(self):
        ACTIONS = {'global': [],
                   'user': [],
                   'object': [],
                   'folder': [],
                   'workflow': [DummyAction('a'), DummyAction('b')],
                  }
        view = self._makeOne()
        tool = view.context.portal_actions = DummyActionsTool(ACTIONS)
        self.assertEqual(view.workflow_actions, ACTIONS['workflow'])

class DummyContext:
    pass

class DummyAction:
    def __init__(self, id):
        self.id = id

class DummySite:
    def __init__(self, paths_to_contexts=()):
        self.paths_to_contexts = paths_to_contexts[:]

    def unrestrictedTraverse(self, path):
        for known, context in self.paths_to_contexts:
            if path == known:
                return context
        raise ValueError('Unknown path: %s' % path)

class DummyPropertiesTool:
    def getProperty(self, key, default):
        return getattr(self, key, default)

class DummyURLTool:
    def __init__(self, site=None, paths_to_contexts=()):
        self.site = site
        self.paths_to_contexts = paths_to_contexts[:]

    def getPortalObject(self):
        return self.site

    def getRelativeContentPath(self, context):
        if context is self.site:
            return ()
        for path, known in self.paths_to_contexts:
            if context is known:
                return path
        raise ValueError('Unknown context: %s' % context)

class DummyMembershipTool:
    pass

class DummyActionsTool:
    def __init__(self, actions=None):
        if actions is None:
            actions = {}
        self.actions = actions.copy()

    def listFilteredActionsFor(self, context):
        return self.actions

class DummyWorkflowTool:
    review_state = 'DUMMY'
    def getInfoFor(self, context, key, default):
        if key == 'review_state':
            return self.review_state

class DummyUser:
    pass

class DummyResponse:
    def __init__(self, **kw):
        self._orig_headers = kw.copy()
        self._set_headers = []

    def getHeader(self, key):
        return self._orig_headers.get(key, '')

    def setHeader(self, key, value):
        self._set_headers.append((key, value))

class DummyRequest:
    def __init__(self):
        self.RESPONSE = DummyResponse()

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UrsineGlobalsTests),
    ))
