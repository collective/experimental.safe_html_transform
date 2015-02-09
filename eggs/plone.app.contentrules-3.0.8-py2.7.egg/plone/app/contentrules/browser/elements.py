from AccessControl import Unauthorized
from zope.i18n import translate

from plone.contentrules.rule.interfaces import IRuleAction
from plone.contentrules.rule.interfaces import IRuleCondition
from plone.contentrules.rule.interfaces import IRuleElementData
from plone.contentrules.engine import utils
from plone.memoize.instance import memoize
from zope.component import getMultiAdapter, getUtilitiesFor, getUtility
from zope.schema.interfaces import IVocabularyFactory

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from plone.app.contentrules import PloneMessageFactory as _, api
from plone.app.contentrules.rule import get_assignments


class ManageElements(BrowserView):
    """Manage elements in a rule
    """

    template = ViewPageTemplateFile('templates/manage-elements.pt')

    def __call__(self):
        redirect = False
        form = self.request.form
        idx = form.get('element_id', 0)

        rule = aq_inner(self.context)
        status = IStatusMessage(self.request)

        if 'form.button.Save' in form:
            self.authorize()
            rule.title = form.get('title', rule.title)
            rule.description = form.get('description', rule.description)
            rule.stop = bool(form.get('stopExecuting', False))
            rule.cascading = bool(form.get('cascading', False))
            rule.enabled = bool(form.get('enabled', False))
            status.addStatusMessage(_(u"Changes saved."), type='info')
        elif 'form.button.EditCondition' in form:
            editview = self.conditions()[idx]['editview']
            self.request.response.redirect(editview)
            redirect = True
        elif 'form.button.DeleteCondition' in form:
            self.authorize()
            del rule.conditions[idx]
            status.addStatusMessage(_(u"Condition deleted."), type='info')
        elif 'form.button.MoveConditionUp' in form:
            self._move_up(rule.conditions, idx)
            status.addStatusMessage(_(u"Condition moved up."), type='info')
        elif 'form.button.MoveConditionDown' in form:
            self._move_down(rule.conditions, idx)
            status.addStatusMessage(_(u"Condition moved down."), type='info')
        elif 'form.button.EditAction' in form:
            editview = self.actions()[idx]['editview']
            self.request.response.redirect(editview)
            redirect = True
        elif 'form.button.DeleteAction' in form:
            self.authorize()
            del rule.actions[idx]
            status.addStatusMessage(_(u"Action deleted."), type='info')
        elif 'form.button.MoveActionUp' in form:
            self._move_up(rule.actions, idx)
            status.addStatusMessage(_(u"Action moved up."), type='info')
        elif 'form.button.MoveActionDown' in form:
            self._move_down(rule.actions, idx)
            status.addStatusMessage(_(u"Action moved down."), type='info')
        elif 'form.button.ApplyOnWholeSite' in form:
            self.globally_assign()
            IStatusMessage(self.request).add(
                                _(u"The rule has been enabled on site root "
                                  u"and all its subfolders"))

        self.view_url = self.base_url + '/@@manage-elements'
        self.rule_title = self.context.title
        self.rule_description = self.context.description
        self.rule_stop = self.context.stop
        self.rule_cascading = self.context.cascading
        self.rule_enabled = self.context.enabled

        if not redirect:
            return self.template()

    def authorize(self):
        authenticator = getMultiAdapter((self.context, self.request),
                                        name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized

    @property
    def base_url(self):
        return aq_inner(self.context).absolute_url()

    def rule_event(self):
        eventsFactory = getUtility(IVocabularyFactory,
                                   name="plone.contentrules.events")
        for e in eventsFactory(self.context):
            if e.value == self.context.event:
                return translate(e.token, context=self.request, domain='plone')

        return "Unknown event" # should not happen

    @memoize
    def actions(self):
        actions = {}
        for name, utility in getUtilitiesFor(IRuleAction):
            actions[name] = utility

        return self._populate_info(self.context.actions, actions, 'action')

    @memoize
    def conditions(self):
        conditions = {}
        for name, utility in getUtilitiesFor(IRuleCondition):
            conditions[name] = utility

        return self._populate_info(self.context.conditions,
                                   conditions, 'condition')

    def addable_conditions(self):
        rule = aq_inner(self.context)

        info = []
        for element in utils.allAvailableConditions(rule.event):
            info.append({'title': element.title,
                         'description': element.description,
                         'addview': element.addview,
                        })

        return info

    def addable_actions(self):
        rule = aq_inner(self.context)

        info = []
        for element in utils.allAvailableActions(rule.event):
            info.append({'title': element.title,
                         'description': element.description,
                         'addview': element.addview,
                        })

        return info

    def assignments(self):
        rule = aq_inner(self.context)
        paths = set(get_assignments(rule))

        site = getToolByName(rule, "portal_url").getPortalObject()
        site_path = '/'.join(site.getPhysicalPath())

        plone_view = getMultiAdapter((rule, self.request), name="plone")

        info = []
        if site_path in paths:
            paths.remove(site_path)
            info.append({'url': site.absolute_url(),
                         'title': site.title_or_id(),
                         'description': site.Description(),
                         'icon': plone_view.getIcon(site),
                        })

        catalog = getToolByName(rule, "portal_catalog")
        for a in catalog(path=dict(query=list(paths), depth=0),
                         sort_on='sortable_title'):
            info.append({'url': a.getURL(),
                         'title': a.Title or a.getId,
                         'description': a.Description,
                         'icon': plone_view.getIcon(a),
                        })

        return info

    def _populate_info(self, elements, meta, namespace):
        """Given an actual list of actions/conditions (elements) and a dict
        mapping element type names to instances (meta), and a namespace
        ('action' or 'condition'), return a list of dicts usable by the view
        template.
        """
        base_url = self.base_url

        info = []

        last = len(elements) - 1
        for idx in range(len(elements)):
            e = elements[idx]

            data = IRuleElementData(e)
            descriptor = meta[data.element]

            editview = None
            if descriptor.editview:
                editview = '%s/++%s++%d/%s' % (base_url, namespace, idx,
                                               descriptor.editview, )

            info.append({'title'      : descriptor.title,
                         'description': descriptor.description,
                         'summary'    : data.summary,
                         'editview'   : editview,
                         'first'      : (idx == 0),
                         'last'       : (idx == last),
                         'idx'        : idx,
                        })
        return info

    def _move_up(self, elements, idx):
        self.authorize()
        element = elements[idx]
        del elements[idx]
        elements.insert(idx - 1, element)

    def _move_down(self, elements, idx):
        self.authorize()
        element = elements[idx]
        del elements[idx]
        elements.insert(idx + 1, element)

    def globally_assign(self):
        self.authorize()
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        api.assign_rule(portal, self.context.__name__)
