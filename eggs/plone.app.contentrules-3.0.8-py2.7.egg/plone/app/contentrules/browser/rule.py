from plone.contentrules.rule.interfaces import IRuleConfiguration
from zope.component import getMultiAdapter
from zope.formlib import form

from Acquisition import aq_parent, aq_inner

from Products.CMFPlone.utils import base_hasattr
from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.rule import Rule
from plone.app.contentrules.browser.formhelper import AddForm, EditForm


class RuleAddForm(AddForm):
    """An add form for rules.
    """
    form_fields = form.FormFields(IRuleConfiguration)
    label = _(u"Add Rule")
    description = _(u"Add a new rule. Once complete, you can manage the "
                     "rule's actions and conditions separately.")
    form_name = _(u"Configure rule")

    def nextURL(self):
        context = aq_parent(aq_inner(self.context))
        url = str(getMultiAdapter((context, self.request), name=u"absolute_url"))
        if base_hasattr(self._parent, '_chosen_name'):
            return '%s/++rule++%s/@@manage-elements' % (url, self._parent._chosen_name)
        else:
            return '%s/@@rules-controlpanel' % url

    def create(self, data):
        rule = Rule()
        form.applyChanges(rule, self.form_fields, data)
        return rule


class RuleEditForm(EditForm):
    """An edit form for rules.
    """
    form_fields = form.FormFields(IRuleConfiguration)
    label = _(u"Edit Rule")
    description = _(u"Edit an existing rule.")
    form_name = _(u"Configure rule")

    def nextURL(self):
        context = aq_parent(aq_inner(self.context))
        url = str(getMultiAdapter((context, self.request), name=u"absolute_url"))
        return url + '/@@rules-controlpanel'
