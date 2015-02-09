from Products.CMFPlone.browser.navigation import PhysicalNavigationBreadcrumbs
from Products.CMFCore.utils import getToolByName

from plone.app.contentrules import PloneMessageFactory


class RuleBreadcrumbs(PhysicalNavigationBreadcrumbs):

    def breadcrumbs(self):
        base = super(RuleBreadcrumbs, self).breadcrumbs()
        portal_url = getToolByName(self.context, 'portal_url')()
        return ({'absolute_url': '%s/@@rules-controlpanel' % portal_url,
                 'Title': PloneMessageFactory('title_manage_contentrules', default=u"Content rules")},
                {'absolute_url': '%s/@@manage-elements' % self.context.absolute_url(),
                 'Title': self.context.title or self.context.id})
