from cgi import escape

from plone.memoize.instance import memoize
from plone.app.content.browser.folderfactories import _allowedTypes
from plone.app.content.browser.interfaces import IContentsPage
from zope.browsermenu.menu import BrowserMenu
from zope.browsermenu.menu import BrowserSubMenuItem
from zope.interface import implements
from zope.component import getMultiAdapter, queryMultiAdapter

from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName, _checkPermission
from Products.CMFDynamicViewFTI.interface import ISelectableBrowserDefault
from Products.CMFPlone import utils
from Products.CMFPlone.interfaces.structure import INonStructuralFolder
from Products.CMFPlone.interfaces.constrains import IConstrainTypes
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes

from plone.app.contentmenu import PloneMessageFactory as _
from plone.app.contentmenu.interfaces import IActionsMenu
from plone.app.contentmenu.interfaces import IActionsSubMenuItem
from plone.app.contentmenu.interfaces import IDisplayMenu
from plone.app.contentmenu.interfaces import IDisplaySubMenuItem
from plone.app.contentmenu.interfaces import IFactoriesMenu
from plone.app.contentmenu.interfaces import IFactoriesSubMenuItem
from plone.app.contentmenu.interfaces import IWorkflowMenu
from plone.app.contentmenu.interfaces import IWorkflowSubMenuItem

try:
    from Products.CMFPlacefulWorkflow import ManageWorkflowPolicies
except ImportError:
    from Products.CMFCore.permissions import \
        ManagePortal as ManageWorkflowPolicies


def _safe_unicode(text):
    if not isinstance(text, unicode):
        text = unicode(text, 'utf-8', 'ignore')
    return text


class ActionsSubMenuItem(BrowserSubMenuItem):
    implements(IActionsSubMenuItem)

    title = _(u'label_actions_menu', default=u'Actions')
    description = _(u'title_actions_menu',
        default=u'Actions for the current content item')
    submenuId = 'plone_contentmenu_actions'

    order = 10
    extra = {'id': 'plone-contentmenu-actions'}

    def __init__(self, context, request):
        BrowserSubMenuItem.__init__(self, context, request)
        self.context_state = getMultiAdapter((context, request),
                                             name='plone_context_state')

    @property
    def action(self):
        folder = self.context
        if not self.context_state.is_structural_folder():
            folder = utils.parent(self.context)
        return folder.absolute_url() + '/folder_contents'

    @memoize
    def available(self):
        if IContentsPage.providedBy(self.request):
            # Don't display action menu on folder_contents page.
            # The cut/copy/paste submenu items are too confusing in this view.
            return False
        actions_tool = getToolByName(self.context, 'portal_actions')
        editActions = actions_tool.listActionInfos(object=self.context,
            categories=('object_buttons',), max=1)
        return len(editActions) > 0

    def selected(self):
        return False


class ActionsMenu(BrowserMenu):
    implements(IActionsMenu)

    def getMenuItems(self, context, request):
        """Return menu item entries in a TAL-friendly form."""
        results = []

        context_state = getMultiAdapter((context, request),
            name='plone_context_state')
        editActions = context_state.actions('object_buttons')
        if not editActions:
            return results

        portal_url = getToolByName(context, 'portal_url')()

        for action in editActions:
            if action['allowed']:
                aid = action['id']
                cssClass = 'actionicon-object_buttons-%s' % aid
                icon = action.get('icon', None)
                if not icon:
                    # allow fallback to action icons tool
                    actionicons = getToolByName(context, 'portal_actionicons', None)
                    if actionicons is not None:
                        icon = actionicons.queryActionIcon('object_buttons', aid)
                        if icon:
                            icon = '%s/%s' % (portal_url, icon)

                results.append({
                    'title': action['title'],
                    'description': '',
                    'action': action['url'],
                    'selected': False,
                    'icon': icon,
                    'extra': {'id': 'plone-contentmenu-actions-' + aid,
                              'separator': None,
                              'class': cssClass},
                    'submenu': None,
                })
        return results


class DisplaySubMenuItem(BrowserSubMenuItem):
    implements(IDisplaySubMenuItem)

    title = _(u'label_choose_template', default=u'Display')
    submenuId = 'plone_contentmenu_display'

    order = 20

    def __init__(self, context, request):
        BrowserSubMenuItem.__init__(self, context, request)
        self.context_state = getMultiAdapter((context, request),
                                             name='plone_context_state')

    @property
    def extra(self):
        return {'id': 'plone-contentmenu-display', 'disabled': self.disabled()}

    @property
    def description(self):
        if self.disabled():
            return _(u'title_remove_index_html_for_display_control',
                default=u'Delete or rename the index_html item to gain full '
                        u'control over how this folder is displayed.')
        else:
            return _(u'title_choose_default_view',
                default=u'Select the view mode for this folder, or set a '
                        u'content item as its default view.')

    @property
    def action(self):
        if self.disabled():
            return ''
        else:
            if self.context_state.is_default_page():
                return self.context_state.parent().absolute_url() + \
                    '/select_default_view'
            else:
                return self.context.absolute_url() + '/select_default_view'

    @memoize
    def available(self):
        if self.disabled():
            return False

        isDefaultPage = self.context_state.is_default_page()

        folder = None
        context = None

        folderLayouts = []
        contextLayouts = []

        # If this is a default page, also get menu items relative to the parent
        if isDefaultPage:
            folder = ISelectableBrowserDefault(utils.parent(self.context),
                                               None)

        context = ISelectableBrowserDefault(self.context, None)

        folderLayouts = []
        folderCanSetLayout = False
        folderCanSetDefaultPage = False

        if folder is not None:
            folderLayouts = folder.getAvailableLayouts()
            folderCanSetLayout = folder.canSetLayout()
            folderCanSetDefaultPage = folder.canSetDefaultPage()

        contextLayouts = []
        contextCanSetLayout = False
        contextCanSetDefaultPage = False

        if context is not None:
            contextLayouts = context.getAvailableLayouts()
            contextCanSetLayout = context.canSetLayout()
            contextCanSetDefaultPage = context.canSetDefaultPage()

        # Show the menu if we either can set a default-page, or we have more
        # than one layout to choose from.
        if (folderCanSetDefaultPage) or \
           (folderCanSetLayout and len(folderLayouts) > 1) or \
           (folder is None and contextCanSetDefaultPage) or \
           (contextCanSetLayout and len(contextLayouts) > 1):
            return True
        else:
            return False

    def selected(self):
        return False

    @memoize
    def disabled(self):
        if IContentsPage.providedBy(self.request):
            return True
        context = self.context
        if self.context_state.is_default_page():
            context = utils.parent(context)
        if not getattr(context, 'isPrincipiaFolderish', False):
            return False
        elif 'index_html' not in context.objectIds():
            return False
        else:
            return True


class DisplayMenu(BrowserMenu):
    implements(IDisplayMenu)

    def getMenuItems(self, obj, request):
        """Return menu item entries in a TAL-friendly form."""
        results = []

        context_state = getMultiAdapter((obj, request),
                                        name='plone_context_state')
        isDefaultPage = context_state.is_default_page()

        parent = None

        folder = None
        context = None

        folderLayouts = []
        contextLayouts = []

        # If this is a default page, also get menu items relative to the parent
        if isDefaultPage:
            parent = utils.parent(obj)
            folder = ISelectableBrowserDefault(parent, None)

        context = ISelectableBrowserDefault(obj, None)

        folderLayouts = []
        folderCanSetLayout = False
        folderCanSetDefaultPage = False

        if folder is not None:
            folderLayouts = folder.getAvailableLayouts()
            folderCanSetLayout = folder.canSetLayout()
            folderCanSetDefaultPage = folder.canSetDefaultPage()

        contextLayouts = []
        contextCanSetLayout = False
        contextCanSetDefaultPage = False

        if context is not None:
            contextLayouts = context.getAvailableLayouts()
            contextCanSetLayout = context.canSetLayout()
            contextCanSetDefaultPage = context.canSetDefaultPage()

        # Short circuit if neither folder nor object will provide us with
        # items
        if not (folderCanSetLayout or folderCanSetDefaultPage or \
                contextCanSetLayout or contextCanSetDefaultPage):
            return []

        # Only show the block "Folder display" and "Item display" separators if
        # they are necessars
        useSeparators = False
        if folderCanSetLayout or folderCanSetDefaultPage:
            if (contextCanSetLayout and len(contextLayouts) > 1) or \
                contextCanSetDefaultPage:
                useSeparators = True

        # 1. If this is a default-page, first render folder options
        if folder is not None:
            folderUrl = parent.absolute_url()

            if useSeparators:
                results.append({
                    'title': _(u'label_current_folder_views',
                                default=u'Folder display'),
                    'description': '',
                    'action': None,
                    'selected': False,
                    'icon': None,
                    'extra': {'id': 'folderHeader',
                              'separator': 'actionSeparator',
                              'class': ''},
                    'submenu': None,
                })

            if folderCanSetLayout:
                for id, title in folderLayouts:
                    results.append({
                        'title': title,
                        'description': '',
                        'action': '%s/selectViewTemplate?templateId=%s' % (
                            folderUrl, id,),
                        'selected': False,
                        'icon': None,
                        'extra': {
                            'id': 'folder-' + id,
                            'separator': None,
                            'class': ''},
                        'submenu': None,
                    })
            # Display the selected item (i.e. the context)
            results.append({
                'title': _(u'label_item_selected',
                    default=u'Item: ${contentitem}',
                    mapping={'contentitem': escape(
                                _safe_unicode(obj.Title()))}),
                'description': '',
                'action': None,
                'selected': True,
                'icon': None,
                'extra': {
                    'id': 'folderDefaultPageDisplay',
                    'separator': 'actionSeparator',
                    'class': 'actionMenuSelected'},
                'submenu': None,
                })
            # Let the user change the selection
            if folderCanSetDefaultPage:
                results.append({
                    'title': _(u'label_change_default_item',
                        default=u'Change content item as default view...'),
                    'description': _(u'title_change_default_view_item',
                        default=u'Change the item used as default view in '
                                u'this folder'),
                    'action': '%s/select_default_page' % (folderUrl,),
                    'selected': False,
                    'icon': None,
                    'extra': {
                        'id': 'folderChangeDefaultPage',
                        'separator': 'actionSeparator',
                        'class': ''},
                    'submenu': None,
                })

        # 2. Render context options
        if context is not None:
            contextUrl = obj.absolute_url()
            selected = context.getLayout()
            defaultPage = context.getDefaultPage()
            layouts = context.getAvailableLayouts()

            if useSeparators:
                results.append({
                    'title': _(u'label_current_item_views',
                                default=u'Item display'),
                    'description': '',
                    'action': None,
                    'selected': False,
                    'icon': None,
                    'extra': {
                        'id': 'contextHeader',
                        'separator': 'actionSeparator',
                        'class': ''},
                    'submenu': None,
                })

            # If context is a default-page in a folder, that folder's views
            # will be shown. Only show context views if there are any to show.

            showLayouts = False
            if not isDefaultPage:
                showLayouts = True
            elif len(layouts) > 1:
                showLayouts = True

            if showLayouts and contextCanSetLayout:
                for id, title in contextLayouts:
                    is_selected = (defaultPage is None and id == selected)
                    results.append({
                        'title': title,
                        'description': '',
                        'action': '%s/selectViewTemplate?templateId=%s' % (
                            contextUrl, id,),
                        'selected': is_selected,
                        'icon': None,
                        'extra': {
                            'id': 'plone-contentmenu-display-' + id,
                            'separator': None,
                            'class': is_selected and 'actionMenuSelected' or ''
                            },
                        'submenu': None,
                    })

            # Allow setting / changing the default-page, unless this is a
            # default-page in a parent folder.
            if not INonStructuralFolder.providedBy(obj):
                if defaultPage is None:
                    if contextCanSetDefaultPage:
                        results.append({
                            'title': _(u'label_choose_item',
                                default=u'Select a content item\n'
                                        u'as default view...'),
                            'description':
                                _(u'title_select_default_view_item',
                                    default=u'Select an item to be used as '
                                            u'default view in this folder...'),
                            'action': '%s/select_default_page' % (contextUrl,),
                            'selected': False,
                            'icon': None,
                            'extra': {
                                'id': 'contextSetDefaultPage',
                                'separator': 'actionSeparator',
                                'class': ''},
                            'submenu': None,
                            })
                else:
                    defaultPageObj = getattr(obj, defaultPage, None)
                    defaultPageTitle = u""
                    if defaultPageObj is not None:
                        if hasattr(aq_base(defaultPageObj), 'Title'):
                            defaultPageTitle = defaultPageObj.Title()
                        else:
                            defaultPageTitle = getattr(aq_base(defaultPageObj),
                                                       'title', u'')

                    results.append({
                        'title': _(u'label_item_selected',
                            default=u'Item: ${contentitem}',
                            mapping={'contentitem': escape(_safe_unicode(
                                defaultPageTitle))}),
                        'description': '',
                        'action': None,
                        'selected': True,
                        'icon': None,
                        'extra': {
                            'id': 'contextDefaultPageDisplay',
                            'separator': 'actionSeparator',
                            'class': ''},
                        'submenu': None,
                    })
                    if contextCanSetDefaultPage:
                        results.append({
                            'title': _(u'label_change_item',
                                default=u'Change content item\nas '
                                        u'default view...'),
                            'description': _(u'title_change_default_view_item',
                                default=u'Change the item used as default '
                                        u'view in this folder'),
                            'action': '%s/select_default_page' % (contextUrl,),
                            'selected': False,
                            'icon': None,
                            'extra': {
                                'id': 'contextChangeDefaultPage',
                                'separator': 'actionSeparator',
                                'class': ''},
                            'submenu': None,
                            })

        return results


class FactoriesSubMenuItem(BrowserSubMenuItem):
    implements(IFactoriesSubMenuItem)

    submenuId = 'plone_contentmenu_factory'
    order = 30
    title = _(u'label_add_new_item', default=u'Add new\u2026')
    description = _(u'title_add_new_items_inside_item',
        default=u'Add new items inside this item')

    def __init__(self, context, request):
        BrowserSubMenuItem.__init__(self, context, request)
        self.context_state = getMultiAdapter((context, request),
                                             name='plone_context_state')

    @property
    def extra(self):
        return {'id': 'plone-contentmenu-factories'}

    @property
    def action(self):
        return '%s/folder_factories' % self._addContext().absolute_url()

    def available(self):
        itemsToAdd = self._itemsToAdd()
        showConstrainOptions = self._showConstrainOptions()
        if self._addingToParent() and not self.context_state.is_default_page():
            return False
        return (len(itemsToAdd) > 0 or showConstrainOptions)

    def selected(self):
        return False

    @memoize
    def _addContext(self):
        if self.context_state.is_structural_folder():
            return self.context
        else:
            return self.context_state.folder()

    @memoize
    def _itemsToAdd(self):
        context = self.context_state.folder()
        return [(context, fti) for fti in self._addableTypesInContext(context)]

    def _addableTypesInContext(self, addContext):
        allowed_types = _allowedTypes(self.request, addContext)
        constrain = IConstrainTypes(addContext, None)
        if constrain is None:
            return allowed_types
        else:
            locallyAllowed = constrain.getLocallyAllowedTypes()
            return [fti for fti in allowed_types
                        if fti.getId() in locallyAllowed]

    @memoize
    def _addingToParent(self):
        add_context_url = self._addContext().absolute_url()
        return (add_context_url != self.context.absolute_url())

    @memoize
    def _showConstrainOptions(self):
        addContext = self._addContext()
        constrain = ISelectableConstrainTypes(addContext, None)
        if constrain is None:
            return False
        elif constrain.canSetConstrainTypes() and \
                constrain.getDefaultAddableTypes():
            return True
        elif len(constrain.getLocallyAllowedTypes()) < \
                len(constrain.getImmediatelyAddableTypes()):
            return True


class FactoriesMenu(BrowserMenu):
    implements(IFactoriesMenu)

    def getMenuItems(self, context, request):
        """Return menu item entries in a TAL-friendly form."""
        factories_view = getMultiAdapter((context, request),
                                         name='folder_factories')

        haveMore = False
        include = None

        addContext = factories_view.add_context()
        allowedTypes = _allowedTypes(request, addContext)

        constraints = IConstrainTypes(addContext, None)
        if constraints is not None:
            include = constraints.getImmediatelyAddableTypes()
            if len(include) < len(allowedTypes):
                haveMore = True

        results = factories_view.addable_types(include=include)

        if haveMore:
            url = '%s/folder_factories' % (addContext.absolute_url(),)
            results.append({
                'title': _(u'folder_add_more', default=u'More\u2026'),
                'description': _(u'Show all available content types'),
                'action': url,
                'selected': False,
                'icon': None,
                'extra': {
                    'id': 'plone-contentmenu-more',
                    'separator': None,
                    'class': ''},
                'submenu': None,
            })

        constraints = ISelectableConstrainTypes(addContext, None)
        if constraints is not None:
            if constraints.canSetConstrainTypes() and \
                    constraints.getDefaultAddableTypes():
                url = '%s/folder_constraintypes_form' % (
                    addContext.absolute_url(),)
                results.append({
                    'title': _(u'folder_add_settings',
                        default=u'Restrictions\u2026'),
                    'description':
                        _(u'title_configure_addable_content_types',
                            default=u'Configure which content types can be '
                                    u'added here'),
                    'action': url,
                    'selected': False,
                    'icon': None,
                    'extra': {
                        'id': 'plone-contentmenu-settings',
                        'separator': None,
                        'class': ''},
                    'submenu': None,
                    })

        # Also add a menu item to add items to the default page
        context_state = getMultiAdapter((context, request),
                                        name='plone_context_state')
        if context_state.is_structural_folder() and context_state.is_default_page():
            results.append({
                'title': _(u'default_page_folder',
                    default=u'Add item to default page'),
                'description':
                    _(u'desc_default_page_folder',
                        default=u'If the default page is also a folder, '
                                u'add items to it from here.'),
                'action': context.absolute_url() + '/@@folder_factories',
                'selected': False,
                'icon': None,
                'extra': {
                    'id': 'plone-contentmenu-add-to-default-page',
                    'separator': None,
                    'class': ''},
                'submenu': None,
                })

        return results


class WorkflowSubMenuItem(BrowserSubMenuItem):
    implements(IWorkflowSubMenuItem)

    MANAGE_SETTINGS_PERMISSION = 'Manage portal'

    title = _(u'label_state', default=u'State:')
    submenuId = 'plone_contentmenu_workflow'
    order = 40

    def __init__(self, context, request):
        BrowserSubMenuItem.__init__(self, context, request)
        self.tools = getMultiAdapter((context, request), name='plone_tools')
        self.context = context
        self.context_state = getMultiAdapter((context, request),
                                             name='plone_context_state')

    @property
    def extra(self):
        state = self.context_state.workflow_state()
        stateTitle = self._currentStateTitle()
        return {'id': 'plone-contentmenu-workflow',
                'class': 'state-%s' % state,
                'state': state,
                'stateTitle': stateTitle}

    @property
    def description(self):
        if self._manageSettings() or len(self._transitions()) > 0:
            return _(u'title_change_state_of_item',
                default=u'Change the state of this item')
        else:
            return u''

    @property
    def action(self):
        if self._manageSettings() or len(self._transitions()) > 0:
            return self.context.absolute_url() + '/content_status_history'
        else:
            return ''

    @memoize
    def available(self):
        return (self.context_state.workflow_state() is not None)

    def selected(self):
        return False

    @memoize
    def _manageSettings(self):
        return self.tools.membership().checkPermission(
            WorkflowSubMenuItem.MANAGE_SETTINGS_PERMISSION, self.context)

    @memoize
    def _transitions(self):
        wf_tool = getToolByName(self.context, 'portal_workflow')
        return wf_tool.listActionInfos(object=self.context, max=1)

    @memoize
    def _currentStateTitle(self):
        state = self.context_state.workflow_state()
        workflows = self.tools.workflow().getWorkflowsFor(self.context)
        if workflows:
            for w in workflows:
                if state in w.states:
                    return w.states[state].title or state


class WorkflowMenu(BrowserMenu):
    implements(IWorkflowMenu)

    # BBB: These actions (url's) existed in old workflow definitions
    # but were never used. The scripts they reference don't exist in
    # a standard installation. We allow the menu to fail gracefully
    # if these are encountered.

    BOGUS_WORKFLOW_ACTIONS = (
        'content_hide_form',
        'content_publish_form',
        'content_reject_form',
        'content_retract_form',
        'content_show_form',
        'content_submit_form',
    )

    def getMenuItems(self, context, request):
        """Return menu item entries in a TAL-friendly form."""
        results = []

        locking_info = queryMultiAdapter((context, request),
                                         name='plone_lock_info')
        if locking_info and locking_info.is_locked_for_current_user():
            return []

        wf_tool = getToolByName(context, 'portal_workflow')
        workflowActions = wf_tool.listActionInfos(object=context)

        for action in workflowActions:
            if action['category'] != 'workflow':
                continue

            cssClass = 'kssIgnore'
            actionUrl = action['url']
            if actionUrl == "":
                actionUrl = '%s/content_status_modify?workflow_action=%s' % (
                    context.absolute_url(), action['id'])
                cssClass = ''

            description = ''

            transition = action.get('transition', None)
            if transition is not None:
                description = transition.description

            for bogus in self.BOGUS_WORKFLOW_ACTIONS:
                if actionUrl.endswith(bogus):
                    if getattr(context, bogus, None) is None:
                        baseUrl = '%s/content_status_modify?workflow_action=%s'
                        actionUrl = baseUrl % (context.absolute_url(),
                                               action['id'])
                        cssClass = ''
                    break

            if action['allowed']:
                results.append({
                    'title': action['title'],
                    'description': description,
                    'action': actionUrl,
                    'selected': False,
                    'icon': None,
                    'extra': {
                        'id': 'workflow-transition-%s' % action['id'],
                        'separator': None,
                        'class': cssClass},
                    'submenu': None,
                })

        url = context.absolute_url()

        if len(results) > 0:
            results.append({
                'title': _(u'label_advanced', default=u'Advanced...'),
                'description': '',
                'action': url + '/content_status_history',
                'selected': False,
                'icon': None,
                'extra': {
                    'id': 'workflow-transition-advanced',
                    'separator': 'actionSeparator',
                    'class': 'kssIgnore'},
                'submenu': None,
            })

        pw = getToolByName(context, 'portal_placeful_workflow', None)
        if pw is not None:
            if _checkPermission(ManageWorkflowPolicies, context):
                results.append({
                    'title': _(u'workflow_policy',
                                default=u'Policy...'),
                    'description': '',
                    'action': url + '/placeful_workflow_configuration',
                    'selected': False,
                    'icon': None,
                    'extra': {'id': 'workflow-transition-policy',
                              'separator': None,
                              'class': 'kssIgnore'},
                    'submenu': None,
                })

        return results
