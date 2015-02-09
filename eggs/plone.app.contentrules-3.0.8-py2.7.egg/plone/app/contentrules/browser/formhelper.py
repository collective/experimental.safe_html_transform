from five.formlib import formbase
from plone.app.form import named_template_adapter
from plone.app.form.validators import null_validator
from zope.component import getMultiAdapter
from zope.event import notify
from zope.formlib import form
from zope.interface import implements
import zope.lifecycleevent

from Acquisition import aq_parent, aq_inner
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.contentrules import PloneMessageFactory as _
from plone.app.contentrules.browser.interfaces import IContentRulesForm

# Add a named template form, which allows us to carry some extra information
# about the referer
_template = ViewPageTemplateFile('templates/contentrules-pageform.pt')
contentrules_named_template_adapter = named_template_adapter(_template)


class AddForm(formbase.AddFormBase):
    """A base add form for content rule.

    Use this for rule elements that require configuration before being added to
    a rule. Element types that do not should use NullAddForm instead.

    Sub-classes should define create() and set the form_fields class variable.

    Notice the suble difference between AddForm and NullAddform in that the
    create template method for AddForm takes as a parameter a dict 'data':

        def create(self, data):
            return MyAssignment(data.get('foo'))

    whereas the NullAddForm has no data parameter:

        def create(self):
            return MyAssignment()
    """

    implements(IContentRulesForm)

    def nextURL(self):
        rule = aq_parent(aq_inner(self.context))
        context = aq_parent(aq_inner(rule))
        url = str(getMultiAdapter((context, self.request), name=u"absolute_url"))
        focus = self.context.id.strip('+')
        return '%s/++rule++%s/@@manage-elements#%s' % (url, rule.__name__, focus)

    @form.action(_(u"label_save", default=u"Save"), name=u'save')
    def handle_save_action(self, action, data):
        self.createAndAdd(data)

    @form.action(_(u"label_cancel", default=u"Cancel"),
                 validator=null_validator,
                 name=u'cancel')
    def handle_cancel_action(self, action, data):
        nextURL = self.nextURL()
        if nextURL:
            self.request.response.redirect(self.nextURL())
        return ''


class NullAddForm(BrowserView):
    """An add view that will add its content immediately, without presenting
    a form.

    You should subclass this for rule elements that do not require any
    configuration before being added, and write a create() method that takes no
    parameters and returns the appropriate assignment instance.
    """

    def __call__(self):
        ob = self.create()
        notify(zope.lifecycleevent.ObjectCreatedEvent(ob))
        self.context.add(ob)
        nextURL = self.nextURL()
        if nextURL:
            self.request.response.redirect(self.nextURL())
        return ''

    def nextURL(self):
        rule = aq_parent(aq_inner(self.context))
        context = aq_parent(aq_inner(rule))
        url = str(getMultiAdapter((context, self.request), name=u"absolute_url"))
        return '%s/++rule++%s/@@manage-elements' % (url, rule.__name__)

    def create(self):
        raise NotImplementedError("concrete classes must implement create()")


class EditForm(formbase.EditFormBase):
    """An edit form for rule elements.
    """

    implements(IContentRulesForm)

    @form.action(_(u"label_save", default=u"Save"),
                 condition=form.haveInputWidgets,
                 name=u'save')
    def handle_save_action(self, action, data):
        if form.applyChanges(self.context, self.form_fields, data, self.adapters):
            notify(zope.lifecycleevent.ObjectModifiedEvent(self.context))
            self.status = "Changes saved"
        else:
            self.status = "No changes"

        nextURL = self.nextURL()
        if nextURL:
            self.request.response.redirect(self.nextURL())
        return ''

    @form.action(_(u"label_cancel", default=u"Cancel"),
                 validator=null_validator,
                 name=u'cancel')
    def handle_cancel_action(self, action, data):
        nextURL = self.nextURL()
        if nextURL:
            self.request.response.redirect(self.nextURL())
        return ''

    def nextURL(self):
        element = aq_inner(self.context)
        rule = aq_parent(element)
        context = aq_parent(rule)
        url = str(getMultiAdapter((context, self.request), name=u"absolute_url"))
        focus = self.context.id.strip('+')
        return '%s/++rule++%s/@@manage-elements#%s' % (url, rule.__name__, focus)
