from zope.component import getUtility
from zope.interface import alsoProvides

from zope.schema.interfaces import IField

from z3c.form.interfaces import IFormLayer
from z3c.form import form, button, field

from plone.memoize.instance import memoize

from plone.registry.interfaces import IRegistry
from plone.registry import Record
from plone.registry import FieldRef

from plone.app.caching.interfaces import _

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

class EditForm(form.Form):
    """General edit form for operations.

    This is not registered as a view directly. Instead, we parameterise it
    manually and return it from the ``publishTraverse()`` method in
    ``controlpanel.py``

    This form can be used in two slightly different ways: to edit "global"
    settings for an operation, or to edit "ruleset-specific" overrides. The
    latter mode is invoked when ``rulesetName`` and ``ruleset`` are set.

    The form fields are built from the records in registry corresponding to
    the operation's ``options`` list, taking the ``prefix`` into account.
    See ``plone.caching`` for a detailed explanation of how the naming scheme
    works.

    If a global record cannot be found, the option is ignored, i.e. no field
    is rendered for it.

    If we are editing ruleset-specific options and a particular ruleset-
    specific option does not exist, we take the global option field as a
    basis, and create a new record on the fly in ``applyChanges()``.

    The only other complication comes from the fact that we need to clone
    the persistent fields for two purposes:

    * Every record's field has the same name -- "value". We need to give it
      a different name in the form, so we clone the field and set a new name.
    * When we create a new ruleset-specific record, we also need a clone of
      the field.

    The ``cloneField()`` method takes care of this for us.

    Once the fields have been set up, the form operations on a dictionary
    context (as returned by ``getContent()``), where the keys are the record
    names.
    """

    template = ViewPageTemplateFile('edit.pt')

    # Keep the ZPublisher happy - would normally be done by the ZCML registration
    __name__ = 'cache-operation-edit'

    def __init__(self, context, request, operationName, operation, rulesetName=None, ruleset=None):
        self.context = context
        self.request = request
        self.operationName = operationName
        self.operation = operation
        self.rulesetName = rulesetName
        self.ruleset = ruleset

    def update(self):

        self.registry = getUtility(IRegistry)

        # If we were using plone.z3cform, this would be done with z2.switch_on()
        if not IFormLayer.providedBy(self.request):
            alsoProvides(self.request, IFormLayer)

        self.request.set('disable_border', True)

        # Create fields for records we actually have. Where applicable, fall
        # back on the  global record if a ruleset-specific record does not
        # yet exist - it will be created later in applyChanges()

        fields = []
        prefix = self.operation.prefix

        for option in self.operation.options:
            newField = None
            fieldName = "%s.%s" % (prefix, option)

            if self.rulesetName:
                rulesetFieldName = "%s.%s.%s" % (prefix, self.rulesetName, option)

                if rulesetFieldName in self.registry.records:
                    newField = self.cloneField(self.registry.records[rulesetFieldName].field)
                    newField.__name__ = rulesetFieldName
                elif fieldName in self.registry.records:
                    newField = self.cloneField(self.registry.records[fieldName].field)
                    newField.__name__ = rulesetFieldName

            else:
                if fieldName in self.registry.records:
                    newField = self.cloneField(self.registry.records[fieldName].field)
                    newField.__name__ = fieldName

            if newField is not None:
                fields.append(newField)

        self.fields = field.Fields(*fields)

        # Set up widgets and actions as normal

        super(EditForm, self).update()

        # Plonify the buttons

        self.actions['save'].addClass('context')
        self.actions['cancel'].addClass('standalone')
        self.actions['clear'].addClass('destructive')

        # Hide 'clear' action if we're not editing a ruleset

        if not self.rulesetName:
            del self.actions['clear']

    # Context

    @memoize
    def getContent(self):
        """Operate on a dictionary context that contains the values for
        all options for which we actually have records.
        """
        context = {}

        prefix = self.operation.prefix
        options = self.operation.options

        for option in options:
            recordName = "%s.%s" % (prefix, option,)

            # If a ruleset-specific record does not exist, we can fall back on
            # a global record, since the per-ruleset records will be created
            # as necessary in applyChanges()

            if self.rulesetName:
                rulesetRecordName = "%s.%s.%s" % (prefix, self.rulesetName, option,)

                if rulesetRecordName in self.registry.records:
                    context[rulesetRecordName] = self.registry[rulesetRecordName]
                elif recordName in self.registry.records:
                    context[rulesetRecordName] = self.registry[recordName]

            else:
                if recordName in self.registry.records:
                    context[recordName] = self.registry[recordName]

        return context

    def applyChanges(self, data):
        """Save changes in the given data dictionary to the registry.
        """

        for key, value in data.items():

            # Lazily create per-ruleset records if necessary
            if key not in self.registry.records:

                # This should only ever happen if we have a not-yet-creted
                # ruleset-specific record
                assert self.rulesetName in key

                # Strip the ruleset name out, leaving the original key - this
                # must exist, otherwise getContent() would not have put it in
                # the data dictionary
                globalKey = self.operation.prefix + key[len(self.operation.prefix) + len(self.rulesetName) + 1:]
                assert globalKey in self.registry.records

                # Create a new record with a FieldRef
                field = self.registry.records[globalKey].field
                self.registry.records[key] = Record(FieldRef(globalKey, field), value)

            else:
                self.registry[key] = value

    def cloneField(self, field):

        # XXX: The field may sometimes not have data for reasons known only
        # to Jim.
        try:
            field._p_activate()
        except AttributeError:
            pass

        clone = field.__class__.__new__(field.__class__)
        clone.__dict__.update(field.__dict__)

        for name, attr in field.__dict__.items():
            if IField.providedBy(attr):
                clone.__dict__[name] = self.cloneField(attr)

        return clone

    # Display

    @property
    def title(self):
        if self.rulesetName:
            return _(u"Edit ${operation} options for Ruleset: ${ruleset}",
                        mapping={'operation': self.operation.title,
                                 'ruleset': self.ruleset.title})
        else:
            return _(u"Edit ${operation} options",
                        mapping={'operation': self.operation.title})

    @property
    def description(self):
        return self.operation.description

    # Buttons/actions

    @button.buttonAndHandler(_(u"Save"), name="save")
    def save(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved."), "info")
        self.request.response.redirect("%s/@@caching-controlpanel#detailed-settings" % self.context.absolute_url())

    @button.buttonAndHandler(_(u"Cancel"), name="cancel")
    def cancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Edit cancelled."), type="info")
        self.request.response.redirect("%s/@@caching-controlpanel#detailed-settings" % self.context.absolute_url())
        return ''

    @button.buttonAndHandler(_(u"Delete settings (use defaults)"), name="clear")
    def clear(self, action):
        for key in self.getContent().keys():
            assert key.startswith("%s.%s." % (self.operation.prefix, self.rulesetName,))

            if key in self.registry.records:
                del self.registry.records[key]

        IStatusMessage(self.request).addStatusMessage(_(u"Ruleset-specific settings removed."), type="info")
        self.request.response.redirect("%s/@@caching-controlpanel#detailed-settings" % self.context.absolute_url())
        return ''
