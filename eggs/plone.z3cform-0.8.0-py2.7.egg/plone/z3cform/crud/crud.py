import sys

from ZODB.POSException import ConflictError
from zope import interface
import zope.event
import zope.lifecycleevent
import zope.publisher.browser
from z3c.form import button
from z3c.form import field
from z3c.form import form
import z3c.form.widget
from z3c.form.interfaces import DISPLAY_MODE, INPUT_MODE, NOVALUE
from zope.browserpage import viewpagetemplatefile

from plone.batching import Batch
from plone.batching.browser import BatchView

from plone.z3cform.widget import singlecheckboxwidget_factory
from plone.z3cform import MessageFactory as _


class ICrudForm(interface.Interface):

    update_schema = interface.Attribute(
        "Editable part of the schema for use in the update form.")

    view_schema = interface.Attribute(
        "Viewable (only) part of the schema for use in the update form.")

    add_schema = interface.Attribute(
        "Schema for use in the add form; defaults to ``update_schema``.")

    editform_factory = interface.Attribute("Factory used for the edit form.")

    addform_factory = interface.Attribute("Factory used for the add form.")

    batch_size = interface.Attribute(
        "Set this to a value greater than 0 to display n items per page.")

    def get_items():
        """Subclasses must a list of all items to edit.

        This list contains tuples of the form ``(id, item)``, where
        the id is a unique identifiers to the items.  The items must
        be adaptable to the schema returned by ``update_schema`` and
        ``view_schema`` methods.
        """

    def add(data):
        """Subclasses must implement this method to create an item for
        the given `data` *and* add it to a container, and return it.

        The `data` mapping corresponds to the schema returned by
        `add_schema`.

        May raise zope.schema.ValidationError to indicate that there's
        a problem with the add form data.
        """

    def remove((id, item)):
        """Subclasses must implement this method to remove the given
        item from the site.

        It's left to the implementing class to notify of
        ``zope.app.container.contained.ObjectRemovedEvent``.
        """

    def before_update(item, data):
        """A hook that gets called before an item is updated.
        """

    def link(item, field):
        """Return a URL for this item's field or None.
        """


class AbstractCrudForm(object):
    """The AbstractCrudForm is not a form but implements methods
    necessary to comply with the ``ICrudForm`` interface:

      >>> from zope.interface.verify import verifyClass
      >>> verifyClass(ICrudForm, AbstractCrudForm)
      True
    """
    interface.implements(ICrudForm)

    update_schema = None
    view_schema = None
    batch_size = 0

    @property
    def add_schema(self):
        return self.update_schema

    def get_items(self):
        raise NotImplementedError

    def add(self, data):
        raise NotImplementedError

    def remove(self, (id, item)):
        raise NotImplementedError

    def before_update(self, item, data):
        pass

    def link(self, item, field):
        return None


class CrudBatchView(BatchView):

    prefix = ''

    def make_link(self, pagenumber):
        return "%s?%spage=%s" % (self.request.getURL(), self.prefix, pagenumber)


class EditSubForm(form.EditForm):
    template = viewpagetemplatefile.ViewPageTemplateFile('crud-row.pt')

    @property
    def prefix(self):
        return 'crud-edit.%s.' % self.content_id

    # These are set by the parent form
    content = None
    content_id = None

    @property
    def fields(self):
        fields = field.Fields(self._select_field())

        crud_form = self.context.context

        update_schema = crud_form.update_schema
        if update_schema is not None:
            fields += field.Fields(update_schema)

        view_schema = crud_form.view_schema
        if view_schema is not None:
            view_fields = field.Fields(view_schema)
            for f in view_fields.values():
                f.mode = DISPLAY_MODE
                # This is to allow a field to appear in both view
                # and edit mode at the same time:
                if not f.__name__.startswith('view_'):
                    f.__name__ = 'view_' + f.__name__
            fields += view_fields

        return fields

    def getContent(self):
        return self.content

    def _select_field(self):
        select_field = field.Field(
            zope.schema.Bool(__name__='select',
                             required=False,
                             title=_(u'select')))
        select_field.widgetFactory[INPUT_MODE] = singlecheckboxwidget_factory
        return select_field

    # XXX: The three following methods, 'getCombinedWidgets',
    # 'getTitleWidgets', and 'getNiceTitles' are hacks to support the
    # page template.  Let's get rid of them.
    def getCombinedWidgets(self):
        """Returns pairs of widgets to improve layout"""
        widgets = self.widgets.items()
        combined = []
        seen = set()
        for name, widget in list(widgets):
            if widget.mode == INPUT_MODE:
                view_widget = self.widgets.get('view_%s' % name)
                if view_widget is not None:
                    combined.append((widget, view_widget))
                    seen.add(view_widget)
                else:
                    combined.append((widget,))
            else:
                if widget not in seen:
                    combined.append((widget,))
        return combined

    def getTitleWidgets(self):
        combinedWidgets = self.getCombinedWidgets()
        widgetsForTitles = [w[0] for w in combinedWidgets]
        return widgetsForTitles

    def getNiceTitles(self):
        widgetsForTitles = self.getTitleWidgets()
        freakList = []
        for item in widgetsForTitles:
            freakList.append(item.field.title)
        return freakList


class EditForm(form.Form):
    label = _(u"Edit")
    template = viewpagetemplatefile.ViewPageTemplateFile('crud-table.pt')

    #exposes the edit sub form for your own derivatives
    editsubform_factory = EditSubForm

    @property
    def prefix(self):
        parent_prefix = getattr(self.context, 'prefix', '')
        return 'crud-edit.' + parent_prefix

    def update(self):
        self._update_subforms()
        super(EditForm, self).update()

    def _update_subforms(self):
        self.subforms = []
        for id, item in self.batch:
            subform = self.editsubform_factory(self, self.request)
            subform.content = item
            subform.content_id = id
            subform.update()
            self.subforms.append(subform)

    @property
    def batch(self):
        items = self.context.get_items()
        batch_size = self.context.batch_size or sys.maxint
        page = int(self.request.get('%spage' % self.prefix, 0))
        return Batch.fromPagenumber(items, batch_size, page+1)

    def render_batch_navigation(self):
        bv = CrudBatchView(self.context, self.request)
        bv.prefix = self.prefix
        return bv(self.batch)

    @button.buttonAndHandler(_('Apply changes'),
                             name='edit',
                             condition=lambda form: form.context.update_schema)
    def handle_edit(self, action):
        success = _(u"Successfully updated")
        partly_success = _(u"Some of your changes could not be applied.")
        status = no_changes = _(u"No changes made.")
        for subform in self.subforms:
            # With the ``extractData()`` call, validation will occur,
            # and errors will be stored on the widgets amongst other
            # places.  After this we have to be extra careful not to
            # call (as in ``__call__``) the subform again, since
            # that'll remove the errors again.  With the results that
            # no changes are applied but also no validation error is
            # shown.
            data, errors = subform.extractData()
            if errors:
                if status is no_changes:
                    status = subform.formErrorsMessage
                elif status is success:
                    status = partly_success
                continue
            del data['select']
            self.context.before_update(subform.content, data)
            changes = subform.applyChanges(data)
            if changes:
                if status is no_changes:
                    status = success
                elif status is subform.formErrorsMessage:
                    status = partly_success

                # If there were changes, we'll update the view widgets
                # again, so that they'll actually display the changes
                for widget in  subform.widgets.values():
                    if widget.mode == DISPLAY_MODE:
                        widget.update()
                        zope.event.notify(z3c.form.widget.AfterWidgetUpdateEvent(widget))
        self.status = status

    @button.buttonAndHandler(_('Delete'), name='delete')
    def handle_delete(self, action):
        selected = self.selected_items()
        if selected:
            self.status = _(u"Successfully deleted items.")
            for id, item in selected:
                try:
                    self.context.remove((id, item))
                except ConflictError:
                    raise
                except:
                    # In case an exception is raised, we'll catch it
                    # and notify the user; in general, this is
                    # unexpected behavior:
                    self.status = _(u'Unable to remove one or more items.')
                    break

            # We changed the amount of entries, so we update the subforms again.
            self._update_subforms()
        else:
            self.status = _(u"Please select items to delete.")

    def selected_items(self):
        tuples = []
        for subform in self.subforms:
            data = subform.widgets['select'].extract()
            if not data or data is NOVALUE:
                continue
            else:
                tuples.append((subform.content_id, subform.content))
        return tuples

class AddForm(form.Form):
    template = viewpagetemplatefile.ViewPageTemplateFile('crud-add.pt')

    label = _(u"Add")
    ignoreContext = True
    ignoreRequest = True

    @property
    def prefix(self):
        parent_prefix = getattr(self.context, 'prefix', '')
        return 'crud-add.' + parent_prefix

    @property
    def fields(self):
        return field.Fields(self.context.add_schema)

    @button.buttonAndHandler(_('Add'), name='add')
    def handle_add(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = form.AddForm.formErrorsMessage
            return
        try:
            item = self.context.add(data)
        except zope.schema.ValidationError, e:
            self.status = e
        else:
            zope.event.notify(zope.lifecycleevent.ObjectCreatedEvent(item))
            self.status = _(u"Item added successfully.")

class NullForm(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def update(self):
        pass

    def render(self):
        return ''
    __call__ = render

class CrudForm(AbstractCrudForm, form.Form):
    template = viewpagetemplatefile.ViewPageTemplateFile('crud-master.pt')
    description = u''

    editform_factory = EditForm
    addform_factory = AddForm

    def update(self):
        super(CrudForm, self).update()

        addform = self.addform_factory(self, self.request)
        editform = self.editform_factory(self, self.request)
        addform.update()
        editform.update()
        self.subforms = [editform, addform]
