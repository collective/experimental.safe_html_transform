from zope.component import queryUtility
from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.engine.interfaces import IRuleAssignable

from AccessControl import getSecurityManager
from Products.Five.browser import BrowserView


class ContentRulesInfo(BrowserView):

    def show_rules_tab(self):
        """Whether or not the rules tab should be shown
        """

        if not IRuleAssignable.providedBy(self.context):
            return False

        if not getSecurityManager().checkPermission('Content rules: Manage rules', self.context):
            return False

        storage = queryUtility(IRuleStorage)
        if not storage:
            return False

        return storage.active
