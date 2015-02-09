import unittest

from Testing.ZopeTestCase.placeless import PlacelessSetup
from Products.PloneTestCase import PloneTestCase as ptc
ptc.setupPloneSite()

from plone.locking.interfaces import ILockable
from zope.browsermenu.interfaces import IBrowserMenu
from zope.component import getUtility
from zope.interface import directlyProvides

from Products.CMFCore.Expression import Expression
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from Products.CMFPlone.interfaces import INonStructuralFolder
from Products.CMFPlone.tests import dummy
from Products.CMFPlone.utils import _createObjectByType

from plone.app.contentmenu.interfaces import IActionsMenu
from plone.app.contentmenu.interfaces import IDisplayMenu
from plone.app.contentmenu.interfaces import IFactoriesMenu
from plone.app.contentmenu.interfaces import IWorkflowMenu


class TestActionsMenu(ptc.PloneTestCase):

    def afterSetUp(self):
        self.menu = getUtility(
            IBrowserMenu, name='plone_contentmenu_actions',
            context=self.folder)
        self.request = self.app.REQUEST

    def testActionsMenuImplementsIBrowserMenu(self):
        self.failUnless(IBrowserMenu.providedBy(self.menu))

    def testActionsMenuImplementsIActionsMenu(self):
        self.failUnless(IActionsMenu.providedBy(self.menu))

    def testActionsMenuFindsActions(self):
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.failUnless('plone-contentmenu-actions-copy' in [a['extra']['id'] for a in actions])


class TestDisplayMenu(ptc.PloneTestCase):

    def afterSetUp(self):
        self.menu = getUtility(
            IBrowserMenu, name='plone_contentmenu_display',
            context=self.folder)
        self.request = self.app.REQUEST

    def testActionsMenuImplementsIBrowserMenu(self):
        self.failUnless(IBrowserMenu.providedBy(self.menu))

    def testActionsMenuImplementsIActionsMenu(self):
        self.failUnless(IDisplayMenu.providedBy(self.menu))

    # Template selection

    def testTemplatesIncluded(self):
        actions = self.menu.getMenuItems(self.folder, self.request)
        templates = [a['extra']['id'] for a in actions]
        self.failUnless('plone-contentmenu-display-folder_listing' in templates)

    def testSingleTemplateIncluded(self):
        self.folder.invokeFactory('Document', 'doc1')
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]['extra']['id'], 'plone-contentmenu-display-document_view')

    def testNonBrowserDefaultReturnsNothing(self):
        f = dummy.Folder()
        self.folder._setObject('f1', f)
        actions = self.menu.getMenuItems(self.folder.f1, self.request)
        self.assertEqual(len(actions), 0)

    def testDefaultPageIncludesParentOnlyWhenItemHasSingleView(self):
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.setDefaultPage('doc1')
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.failUnless('folderDefaultPageDisplay' in
                        [a['extra']['id'] for a in actions])
        self.failIf('document_view' in [a['extra']['id'] for a in actions])

    def testDefaultPageIncludesParentAndItemViewsWhenItemHasMultipleViews(
        self):
        fti = self.portal.portal_types['Document']
        documentViews = fti.view_methods + ('base_view',)
        fti.manage_changeProperties(view_methods=documentViews)
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.setDefaultPage('doc1')
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.failUnless('folderDefaultPageDisplay' in
                        [a['extra']['id'] for a in actions])
        self.failUnless('plone-contentmenu-display-document_view' in [a['extra']['id'] for a in actions])
        self.failUnless('plone-contentmenu-display-base_view' in [a['extra']['id'] for a in actions])

    def testCurrentTemplateSelected(self):
        self.folder.getLayout()
        actions = self.menu.getMenuItems(self.folder, self.request)
        selected = [a['extra']['id'] for a in actions if a['selected']]
        self.assertEqual(selected, ['plone-contentmenu-display-folder_listing'])

    # Default-page selection

    def testFolderCanSetDefaultPage(self):
        self.folder.invokeFactory('Folder', 'f1')
        self.failUnless(self.folder.f1.canSetDefaultPage())
        actions = self.menu.getMenuItems(self.folder.f1, self.request)
        self.failUnless('contextSetDefaultPage' in
                        [a['extra']['id'] for a in actions])

    def testWithCanSetDefaultPageFalse(self):
        self.folder.invokeFactory('Folder', 'f1')
        self.folder.f1.manage_permission('Modify view template', ('Manager',))
        self.failIf(self.folder.f1.canSetDefaultPage())
        actions = self.menu.getMenuItems(self.folder.f1, self.request)
        self.failIf('contextSetDefaultPage' in
                    [a['extra']['id'] for a in actions])

    def testSelectItemNotIncludedInNonStructuralFolder(self):
        self.folder.invokeFactory('Folder', 'f1')
        directlyProvides(self.folder.f1, INonStructuralFolder)
        actions = self.menu.getMenuItems(self.folder.f1, self.request)
        self.failIf('contextSetDefaultPage' in
                    [a['extra']['id'] for a in actions])

    def testDefaultPageSelectedAndOverridesLayout(self):
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.setDefaultPage('doc1')
        actions = self.menu.getMenuItems(self.folder, self.request)
        selected = [a['extra']['id'] for a in actions if a['selected']]
        self.assertEqual(selected, ['contextDefaultPageDisplay'])

    def testDefaultPageCanBeChangedInContext(self):
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.setDefaultPage('doc1')
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.failUnless('contextChangeDefaultPage' in
                        [a['extra']['id'] for a in actions])

    def testDefaultPageCanBeChangedInFolder(self):
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.setDefaultPage('doc1')
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.failUnless('folderChangeDefaultPage' in
                        [a['extra']['id'] for a in actions])
        self.failIf('contextChangeDefaultPage' in
                    [a['extra']['id'] for a in actions])

    # Headers/separators

    def testSeparatorsIncludedWhenViewingDefaultPageWithViews(self):
        fti = self.portal.portal_types['Document']
        documentViews = fti.view_methods + ('base_view',)
        fti.manage_changeProperties(view_methods=documentViews)
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.setDefaultPage('doc1')
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        ids = [a['extra']['id'] for a in actions]
        self.failUnless('folderHeader' in ids)
        self.failUnless('contextHeader' in ids)

    def testSeparatorsNotIncludedWhenViewingDefaultPageWithoutViews(self):
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.setDefaultPage('doc1')
        self.assertEqual(len(self.folder.doc1.getAvailableLayouts()), 1)
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        ids = [a['extra']['id'] for a in actions]
        self.failIf('folderHeader' in ids)
        self.failIf('contextHeader' in ids)

    def testSeparatorsNotDisplayedWhenViewingFolder(self):
        fti = self.portal.portal_types['Document']
        documentViews = fti.view_methods + ('base_view',)
        fti.manage_changeProperties(view_methods=documentViews)
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.setDefaultPage('doc1')
        actions = self.menu.getMenuItems(self.folder, self.request)
        ids = [a['extra']['id'] for a in actions]
        self.failIf('folderHeader' in ids)
        self.failIf('contextHeader' in ids)

    # Regressions

    def testDefaultPageTemplateTitle(self):
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.doc1.setTitle("New Document")
        self.folder.setDefaultPage('doc1')
        actions = self.menu.getMenuItems(self.folder, self.request)
        changeAction = [x for x in actions if
                        x['extra']['id'] == 'contextDefaultPageDisplay'][0]
        changeAction['title'].default
        self.assertEquals(u"New Document",
                          changeAction['title'].mapping['contentitem'])


class TestFactoriesMenu(ptc.PloneTestCase):

    def afterSetUp(self):
        self.folder.invokeFactory('Document', 'doc1')
        self.menu = getUtility(
            IBrowserMenu, name='plone_contentmenu_factory',
            context=self.folder)
        self.request = self.app.REQUEST

    def testMenuImplementsIBrowserMenu(self):
        self.failUnless(IBrowserMenu.providedBy(self.menu))

    def testMenuImplementsIFactoriesMenu(self):
        self.failUnless(IFactoriesMenu.providedBy(self.menu))

    def testMenuIncludesFactories(self):
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.failUnless('image' in [a['extra']['id'] for a in actions])

    def testAddViewExpressionUsedInMenu(self):
        self.portal.portal_types['Image']._setPropValue(
            'add_view_expr', 'string:custom_expr')
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.failUnless('custom_expr' in [a['action'] for a in actions])
        self.failUnless(
            '%s/createObject?type_name=File' % self.folder.absolute_url()
            in [a['action'] for a in actions])

    def testFrontPageExpressionContext(self):
        # If the expression context uses the front-page instead of the
        # folder using the front-page, then the expression values will
        # be incorrect.
        self.portal.portal_types['Event']._setPropValue(
            'add_view_expr', 'string:${folder_url}/+/addATEvent')
        self.loginAsPortalOwner()
        actions = self.menu.getMenuItems(
            self.portal.events.aggregator, self.request)
        self.failUnless(
            'http://nohost/plone/events/+/addATEvent' in \
                [a['action'] for a in actions])
        self.failIf(
            'http://nohost/plone/events/aggregator/+/addATEvent' in
            [a['action'] for a in actions])

    def testTypeNameIsURLQuoted(self):
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.failUnless(
            self.folder.absolute_url() + '/createObject?type_name=News+Item'
            in [a['action'] for a in actions])

    def testMenuIncludesFactoriesOnNonFolderishContext(self):
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        img = None
        for a in actions:
            if a['extra']['id'] == 'image':
                img = a
                break
        self.failIf(img is None)
        action = img['action']
        url = self.folder.absolute_url()
        self.failUnless(action.startswith(url))
        url = self.folder.doc1.absolute_url()
        self.failIf(action.startswith(url))

    def testNoAddableTypes(self):
        actions = self.menu.getMenuItems(self.portal, self.request)
        self.assertEqual(len(actions), 0)

        # set no types for folders and check the menu is not shown
        folder_fti = self.portal.portal_types['Folder']
        folder_fti.manage_changeProperties(
            filter_content_types=True, allowed_content_types=[])
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.assertEqual(len(actions), 0)

    def testConstrainTypes(self):
        constraints = ISelectableConstrainTypes(self.folder)
        constraints.setConstrainTypesMode(1)
        constraints.setLocallyAllowedTypes(('Document',))
        constraints.setImmediatelyAddableTypes(('Document',))
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0]['extra']['id'], 'document')
        self.assertEqual(actions[1]['extra']['id'], 'plone-contentmenu-settings')

    def testSettingsIncluded(self):
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.assertEqual(actions[-1]['extra']['id'], 'plone-contentmenu-settings')

    def testSettingsNotIncludedWhereNotSupported(self):
        self.folder.manage_permission('Modify constrain types', ('Manager',))
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.failIf('_settings' in [a['extra']['id'] for a in actions])

    def testMoreIncluded(self):
        constraints = ISelectableConstrainTypes(self.folder)
        constraints.setConstrainTypesMode(1)
        constraints.setLocallyAllowedTypes(('Document', 'Image',))
        constraints.setImmediatelyAddableTypes(('Document',))
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.failIf('image' in [a['extra']['id'] for a in actions])
        self.failUnless('document' in [a['extra']['id'] for a in actions])
        self.failUnless('plone-contentmenu-more' in [a['extra']['id'] for a in actions])
        self.failUnless('plone-contentmenu-settings' in [a['extra']['id'] for a in actions])

    def testMoreNotIncludedWhenNotNecessary(self):
        constraints = ISelectableConstrainTypes(self.folder)
        constraints.setConstrainTypesMode(1)
        constraints.setLocallyAllowedTypes(('Document',))
        constraints.setImmediatelyAddableTypes(('Document',))
        actions = self.menu.getMenuItems(self.folder, self.request)
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0]['extra']['id'], 'document')
        self.assertEqual(actions[1]['extra']['id'], 'plone-contentmenu-settings')

    def testNonStructualFolderShowsParent(self):
        self.folder.invokeFactory('Folder', 'folder1')
        directlyProvides(self.folder.folder1, INonStructuralFolder)
        constraints = ISelectableConstrainTypes(self.folder.folder1)
        constraints.setConstrainTypesMode(1)
        constraints.setLocallyAllowedTypes(('Document',))
        constraints.setImmediatelyAddableTypes(('Document',))
        actions = self.menu.getMenuItems(self.folder.folder1, self.request)
        action_ids = [a['extra']['id'] for a in actions]
        self.failUnless('event' in action_ids)

    def testImgConditionalOnTypeIcon(self):
        """The <img> element should not render if the content type has
        no icon expression"""
        folder_fti = self.portal.portal_types['Folder']
        folder_fti.manage_changeProperties(icon_expr='')
        for item in self.menu.getMenuItems(self.folder, self.request):
            if item['id'] == folder_fti.getId():
                break
        self.failIf(item['icon'])


class TestWorkflowMenu(ptc.PloneTestCase):

    def afterSetUp(self):
        self.folder.invokeFactory('Document', 'doc1')
        self.menu = getUtility(
            IBrowserMenu, name='plone_contentmenu_workflow',
            context=self.folder)
        self.request = self.app.REQUEST

    def testMenuImplementsIBrowserMenu(self):
        self.failUnless(IBrowserMenu.providedBy(self.menu))

    def testMenuImplementsIActionsMenu(self):
        self.failUnless(IWorkflowMenu.providedBy(self.menu))

    def testMenuIncludesActions(self):
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.failUnless('workflow-transition-submit' in
                        [a['extra']['id'] for a in actions])
        self.failUnless(('http://nohost/plone/Members/test_user_1_/doc1/'
                         'content_status_modify?workflow_action=submit')
                        in [a['action'] for a in actions])

        # Let us try that again but with an empty url action, like is
        # usual in older workflows, and which is nice to keep
        # supporting.
        context = self.folder.doc1
        wf_tool = getToolByName(context, "portal_workflow")
        submit = wf_tool.plone_workflow.transitions['submit']
        submit.actbox_url = ""
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.failUnless('workflow-transition-submit' in
                        [a['extra']['id'] for a in actions])
        self.failUnless(('http://nohost/plone/Members/test_user_1_/doc1/'
                         'content_status_modify?workflow_action=submit') in
                        [a['action'] for a in actions])

    def testNoTransitions(self):
        self.logout()
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.assertEqual(len(actions), 0)

    def testLockedItem(self):
        membership_tool = getToolByName(self.folder, 'portal_membership')
        membership_tool.addMember('anotherMember', 'secret', ['Member'], [])
        locking = ILockable(self.folder.doc1)
        locking.lock()
        self.login('anotherMember')
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.assertEqual(len(actions), 0)

    def testAdvancedIncluded(self):
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        url = self.folder.doc1.absolute_url() + '/content_status_history'
        self.failUnless(url in [a['action'] for a in actions])

    def testPolicyIncludedIfCMFPWIsInstalled(self):
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        url = self.folder.doc1.absolute_url(
            ) + '/placeful_workflow_configuration'
        self.failIf(url in [a['action'] for a in actions])
        self.portal.portal_quickinstaller.installProduct('CMFPlacefulWorkflow')

        # item needs permission
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.failIf(url in [a['action'] for a in actions])
        self.loginAsPortalOwner()
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.failUnless(url in [a['action'] for a in actions])


class TestContentMenu(ptc.PloneTestCase):

    def afterSetUp(self):
        self.menu = getUtility(
            IBrowserMenu, name='plone_contentmenu', context=self.folder)
        self.request = self.app.REQUEST

    # Actions sub-menu

    def testActionsSubMenuIncluded(self):
        items = self.menu.getMenuItems(self.folder, self.request)
        actionsMenuItem = [i for i in items if
                           i['extra']['id'] == 'plone-contentmenu-actions'][0]
        self.assertEqual(actionsMenuItem['action'],
                         self.folder.absolute_url() + '/folder_contents')
        self.failUnless(len(actionsMenuItem['submenu']) > 0)

    # Display sub-menu

    def testDisplayMenuIncluded(self):
        items = self.menu.getMenuItems(self.folder, self.request)
        displayMenuItem = [i for i in items if
                           i['extra']['id'] == 'plone-contentmenu-display'][0]
        self.assertEqual(displayMenuItem['action'],
                         self.folder.absolute_url() + '/select_default_view')
        self.failUnless(len(displayMenuItem['submenu']) > 0)

    def testDisplayMenuNotIncludedIfContextDoesNotSupportBrowserDefault(self):
        # We need to create an object that does not have
        # IBrowserDefault enabled
        _createObjectByType('ATListCriterion', self.folder, 'c1')
        items = self.menu.getMenuItems(self.folder.c1, self.request)
        self.assertEqual([i for i in items if
                          i['extra']['id'] == 'plone-contentmenu-display'], [])

    def testWhenContextDoesNotSupportSelectableBrowserDefault(self):
        """Display Menu Show Folder Default Page When Context Does Not
        Support Selectable Browser Default"""
        # We need to create an object that is not
        # ISelectableBrowserDefault aware
        _createObjectByType('ATListCriterion', self.folder, 'c1')
        self.folder.c1.setTitle('Foo')
        self.folder.setDefaultPage('c1')
        items = self.menu.getMenuItems(self.folder.c1, self.request)
        displayMenuItem = [i for i in items if
                           i['extra']['id'] == 'plone-contentmenu-display'][0]
        selected = [a for a in displayMenuItem['submenu']
                    if a['selected']][0]
        self.assertEqual(u'Foo', selected['title'].mapping['contentitem'])

    def testDisplayMenuNotIncludedIfNoActionsAvailable(self):
        self.folder.invokeFactory('Document', 'doc1')
        items = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.assertEqual([i for i in items if
                          i['extra']['id'] == 'plone-contentmenu-display'], [])

    def testDisplayMenuDisabledIfIndexHtmlInFolder(self):
        self.folder.invokeFactory('Document', 'index_html')
        items = self.menu.getMenuItems(self.folder, self.request)
        displayMenuItems = [i for i in items if
                            i['extra']['id'] == 'plone-contentmenu-display']
        self.assertEqual(len(displayMenuItems), 0)

    def testDisplayMenuDisabledIfIndexHtmlInFolderAndContextIsIndexHtml(self):
        self.folder.invokeFactory('Document', 'index_html')
        items = self.menu.getMenuItems(self.folder.index_html, self.request)
        displayMenuItems = [i for i in items if
                            i['extra']['id'] == 'plone-contentmenu-display']
        self.assertEqual(len(displayMenuItems), 0)

    def testDisplayMenuAddPrefixFolderForContainerPart(self):
        prefix = 'folder-'
        self.folder.invokeFactory('Folder', 'subfolder1')
        self.folder.setDefaultPage('subfolder1')
        items = self.menu.getMenuItems(self.folder.subfolder1, self.request)
        displayMenuItems = [i for i in items if
                            i['extra']['id'] == 'plone-contentmenu-display'][0]
        extras = [i['extra'] for i in displayMenuItems['submenu']]
        for extra in extras[1:]:
            if not extra['separator'] is None:
                break
            else:
                self.assertEqual(extra['id'][0:len(prefix)], prefix)

    # Add sub-menu

    def testAddMenuIncluded(self):
        items = self.menu.getMenuItems(self.folder, self.request)
        factoriesMenuItem = [
            i for i in items if
            i['extra']['id'] == 'plone-contentmenu-factories'][0]
        self.assertEqual(factoriesMenuItem['action'],
                         self.folder.absolute_url() + '/folder_factories')
        self.failUnless(len(factoriesMenuItem['submenu']) > 0)

    def testAddMenuNotIncludedIfNothingToAdd(self):
        self.logout()
        items = self.menu.getMenuItems(self.folder, self.request)
        self.assertEqual(
            [i for i in items if
             i['extra']['id'] == 'plone-contentmenu-factories'], [])

    def testAddMenuWithNothingToAddButWithAvailableConstrainSettings(self):
        self.folder.setConstrainTypesMode(1)
        self.folder.setLocallyAllowedTypes(())
        self.folder.setImmediatelyAddableTypes(())
        items = self.menu.getMenuItems(self.folder, self.request)
        factoriesMenuItem = [
            i for i in items if
            i['extra']['id'] == 'plone-contentmenu-factories'][0]
        self.assertEqual(len(factoriesMenuItem['submenu']), 1)
        self.assertEqual(factoriesMenuItem['submenu'][0]['extra']['id'],
                         'plone-contentmenu-settings')

    def testAddMenuWithNothingToAddButWithAvailableMorePage(self):
        self.folder.setConstrainTypesMode(1)
        self.folder.setLocallyAllowedTypes(('Document',))
        self.folder.setImmediatelyAddableTypes(())
        self.folder.manage_permission('Modify constrain types', ('Manager',))
        items = self.menu.getMenuItems(self.folder, self.request)
        factoriesMenuItem = [
            i for i in items if
            i['extra']['id'] == 'plone-contentmenu-factories'][0]
        self.assertEqual(len(factoriesMenuItem['submenu']), 1)
        self.assertEqual(factoriesMenuItem['submenu'][0]['extra']['id'],
                         'plone-contentmenu-more')

    def testAddMenuRelativeToNonStructuralFolder(self):
        self.folder.invokeFactory('Folder', 'f1')
        directlyProvides(self.folder.f1, INonStructuralFolder)
        items = self.menu.getMenuItems(self.folder.f1, self.request)
        factoriesMenuItem = [i for i in items if
                             i['extra']['id'] == 'plone-contentmenu-factories']
        self.failIf(factoriesMenuItem)

    def testAddMenuWithAddViewExpr(self):
        # we need a dummy to test this - should test that if the item does not
        # support constrain types and there is
        self.folder.setConstrainTypesMode(1)
        self.folder.setLocallyAllowedTypes(('Document',))
        self.folder.setImmediatelyAddableTypes(('Document',))
        self.folder.manage_permission('Modify constrain types', ('Manager',))
        self.portal.portal_types['Document']._setPropValue(
            'add_view_expr', 'string:custom_expr')
        items = self.menu.getMenuItems(self.folder, self.request)
        factoriesMenuItem = [
            i for i in items if
            i['extra']['id'] == 'plone-contentmenu-factories'][0]
        self.assertEqual(factoriesMenuItem['submenu'][0]['action'],
                         'custom_expr')

    # Workflow sub-menu

    def testWorkflowMenuIncluded(self):
        items = self.menu.getMenuItems(self.folder, self.request)
        workflowMenuItem = [
            i for i in items if
            i['extra']['id'] == 'plone-contentmenu-workflow'][0]
        self.assertEqual(
            workflowMenuItem['action'],
            self.folder.absolute_url() + '/content_status_history')
        self.failUnless(len(workflowMenuItem['submenu']) > 0)

    def testWorkflowMenuWithNoTransitionsDisabled(self):
        self.logout()
        items = self.menu.getMenuItems(self.folder, self.request)
        workflowMenuItem = [
            i for i in items if
            i['extra']['id'] == 'plone-contentmenu-workflow'][0]
        self.assertEqual(workflowMenuItem['action'], '')

    # XXX: Unable to write a proper test so far
    def DISABLED_testWorkflowMenuWithNoTransitionsEnabledAsManager(self):
        # set workflow guard condition that fails, so there are no transitions.
        # then show that manager will get a drop-down with settings whilst
        # regular users won't

        self.portal.portal_workflow.doActionFor(self.folder, 'hide')
        wf = self.portal.portal_workflow['folder_workflow']
        wf.transitions['show'].guard.expr = Expression('python: False')
        wf.transitions['publish'].guard.expr = Expression('python: False')

        items = self.menu.getMenuItems(self.folder, self.request)
        workflowMenuItem = [
            i for i in items if
            i['extra']['id'] == 'plone-contentmenu-workflow'][0]

        # A regular user doesn't see any actions
        self.failUnless(workflowMenuItem['action'] == '')
        self.failUnless(workflowMenuItem['submenu'] is None)

        self.fail('Unable to write a proper test so far')

    def testWorkflowMenuWithNoWorkflowNotIncluded(self):
        self.portal.portal_workflow.setChainForPortalTypes(('Document',), ())
        self.folder.invokeFactory('Document', 'doc1')
        actions = self.menu.getMenuItems(self.folder.doc1, self.request)
        self.failIf('plone_contentmenu_workflow' in
                    [a['extra']['id'] for a in actions])


class TestDisplayViewsMenu(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        # BBB for Zope 2.12
        try:
            from Zope2.App import zcml
        except ImportError:
            from Products.Five import zcml
        import Products.Five
        import plone.app.contentmenu
        zcml.load_config("meta.zcml", Products.Five)
        zcml.load_config('configure.zcml', plone.app.contentmenu)
        zcml.load_config('tests.zcml', plone.app.contentmenu)
        self.menu = getUtility(IBrowserMenu, 'plone_displayviews')

    def _getMenuItemByAction(self, action):
        from zope.publisher.browser import TestRequest
        context = dummy.Dummy()
        request = TestRequest()
        return self.menu.getMenuItemByAction(context, request, action)

    def testInterface(self):
        """A DisplayViewsMenu implements an extended interface"""
        from plone.app.contentmenu.interfaces import IDisplayViewsMenu
        self.assertTrue(IDisplayViewsMenu.providedBy(self.menu))

    def testSimpleAction(self):
        """Retrieve a registered IBrowserMenuItem"""
        item = self._getMenuItemByAction('foo.html')
        self.assertFalse(item is None)
        self.assertEqual(item.title, 'Test Menu Item')

    def testViewAction(self):
        """Retrieve a registered IBrowserMenuItem"""
        item = self._getMenuItemByAction('bar.html')
        self.assertFalse(item is None)
        self.assertEqual(item.title, 'Another Test Menu Item')

        item = self._getMenuItemByAction('@@bar.html')
        self.assertEqual(item.title, 'Another Test Menu Item')
        item = self._getMenuItemByAction('++view++bar.html')
        self.assertEqual(item.title, 'Another Test Menu Item')

    def testNonExisting(self):
        """Attempt to retrieve a non-registered IBrowserMenuItem"""
        item = self._getMenuItemByAction('nonesuch.html')
        self.assertTrue(item is None)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestActionsMenu))
    suite.addTest(makeSuite(TestDisplayMenu))
    suite.addTest(makeSuite(TestFactoriesMenu))
    suite.addTest(makeSuite(TestWorkflowMenu))
    suite.addTest(makeSuite(TestContentMenu))
    suite.addTest(makeSuite(TestDisplayViewsMenu))
    return suite
