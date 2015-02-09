CRUD (Create, Read, Update and Delete) forms
============================================

This module provides an abstract base class to create CRUD forms.
By default, such forms provide a tabular view of multiple objects, whose
attributes can be edited in-place.

Please refer to the ``ICrudForm`` interface for more details.

  >>> from plone.z3cform.crud import crud

Setup
-----

  >>> from plone.z3cform.tests import setup_defaults
  >>> setup_defaults()

A simple form
-------------

First, let's define an interface and a class to play with:

  >>> from zope import interface, schema
  >>> class IPerson(interface.Interface) :
  ...     name = schema.TextLine()
  ...     age = schema.Int()

  >>> class Person(object):
  ...     interface.implements(IPerson)
  ...     def __init__(self, name=None, age=None):
  ...         self.name, self.age = name, age
  ...     def __repr__(self):
  ...         return "<Person with name=%r, age=%r>" % (self.name, self.age)

For this test, we take the the name of our persons as keys in our
storage:

  >>> storage = {'Peter': Person(u'Peter', 16),
  ...            'Martha': Person(u'Martha', 32)}

Our simple form looks like this:

  >>> class MyForm(crud.CrudForm):
  ...     update_schema = IPerson
  ... 
  ...     def get_items(self):
  ...         return sorted(storage.items(), key=lambda x: x[1].name)
  ... 
  ...     def add(self, data):
  ...         person = Person(**data)
  ...         storage[str(person.name)] = person
  ...         return person
  ... 
  ...     def remove(self, (id, item)):
  ...         del storage[id]

This is all that we need to render a combined edit add form containing
all our items:

  >>> from plone.z3cform.tests import TestRequest
  >>> print MyForm(None, TestRequest())() \
  ... # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
  <div class="crud-form">...Martha...Peter...</div>

Editing items with our form
---------------------------

Before we start with editing objects, let's log all events that the
form fires for us:

  >>> from zope.lifecycleevent.interfaces import IObjectModifiedEvent
  >>> from plone.z3cform.tests import create_eventlog
  >>> log = create_eventlog(IObjectModifiedEvent)

  >>> request = TestRequest()
  >>> request.form['crud-edit.Martha.widgets.select-empty-marker'] = u'1'
  >>> request.form['crud-edit.Peter.widgets.select-empty-marker'] = u'1'
  >>> request.form['crud-edit.Martha.widgets.name'] = u'Martha'
  >>> request.form['crud-edit.Martha.widgets.age'] = u'55'
  >>> request.form['crud-edit.Peter.widgets.name'] = u'Franz'
  >>> request.form['crud-edit.Peter.widgets.age'] = u'16'
  >>> request.form['crud-edit.form.buttons.edit'] = u'Apply changes'
  >>> html = MyForm(None, request)()
  >>> "Successfully updated" in html
  True

Two modified events should have been fired:

  >>> event1, event2 = log.pop(), log.pop()
  >>> storage['Peter'] in (event1.object, event2.object)
  True
  >>> storage['Martha'] in (event1.object, event2.object)
  True
  >>> log
  []

If we don't make any changes, we'll get a message that says so:

  >>> html = MyForm(None, request)()
  >>> "No changes made" in html
  True
  >>> log
  []

Now that we renamed Peter to Franz, it would be also nice to have
Franz use 'Franz' as the id in the storage, wouldn't it?

  >>> storage['Peter']
  <Person with name=u'Franz', age=16>

We can override the CrudForm's ``before_update`` method to perform a
rename whenever the name of a person is changed:

  >>> class MyRenamingForm(MyForm):
  ...     def before_update(self, item, data):
  ...         if data['name'] != item.name:
  ...             del storage[item.name]
  ...             storage[str(data['name'])] = item

Let's rename Martha to Maria.  This will give her another key in our
storage:

  >>> request.form['crud-edit.Martha.widgets.name'] = u'Maria'
  >>> html = MyRenamingForm(None, request)()
  >>> "Successfully updated" in html
  True
  >>> log.pop().object == storage['Maria']
  True
  >>> log
  []
  >>> sorted(storage.keys())
  ['Maria', 'Peter']

Next, we'll submit the form for edit, but we'll make no changes.
Instead, we'll select one time.  This shouldn't do anything, since we
clicked the 'Apply changes' button:

  >>> request.form['crud-edit.Maria.widgets.name'] = u'Maria'
  >>> request.form['crud-edit.Maria.widgets.age'] = u'55'
  >>> request.form['crud-edit.Maria.widgets.select'] = [u'selected']
  >>> html = MyRenamingForm(None, request)()
  >>> "No changes" in html
  True
  >>> log
  []

And what if we do have changes *and* click the checkbox?

  >>> request.form['crud-edit.Maria.widgets.age'] = u'50'
  >>> html = MyRenamingForm(None, request)()
  >>> "Successfully updated" in html
  True
  >>> log.pop().object == storage['Maria']
  True
  >>> log
  []

If we omit the name, we'll get an error:

  >>> request.form['crud-edit.Maria.widgets.name'] = u''
  >>> html = MyRenamingForm(None, request)()
  >>> "There were some errors" in html
  True
  >>> "Required input is missing" in html
  True

We expect an error message in the title cell of Maria:

  >>> checkbox_pos = html.index('crud-edit.Maria.widgets.select-empty-marker')
  >>> "Required input is missing" in html[checkbox_pos:]
  True

Delete an item with our form
----------------------------

We can delete an item by selecting the item we want to delete and
clicking the "Delete" button:

  >>> request = TestRequest()
  >>> request.form['crud-edit.Peter.widgets.select'] = ['selected']
  >>> request.form['crud-edit.form.buttons.delete'] = u'Delete'
  >>> html = MyForm(None, request)()
  >>> "Successfully deleted items" in html
  True
  >>> 'Franz' in html
  False
  >>> storage
  {'Maria': <Person with name=u'Maria', age=50>}

Add an item with our form
-------------------------

  >>> from zope.lifecycleevent.interfaces import IObjectCreatedEvent
  >>> from plone.z3cform.tests import create_eventlog
  >>> log = create_eventlog(IObjectCreatedEvent)

  >>> request = TestRequest()
  >>> request.form['crud-add.form.widgets.name'] = u'Daniel'
  >>> request.form['crud-add.form.widgets.age'] = u'28'
  >>> request.form['crud-add.form.buttons.add'] = u'Add'
  >>> html = MyForm(None, request)()
  >>> "Item added successfully" in html
  True

Added items should show up right away:

  >>> "Daniel" in html
  True

  >>> storage['Daniel']
  <Person with name=u'Daniel', age=28>
  >>> log.pop().object == storage['Daniel']
  True
  >>> log
  []

What if we try to add "Daniel" twice?  Our current implementation of
the add form will simply overwrite the data:

  >>> save_daniel = storage['Daniel']
  >>> html = MyForm(None, request)()
  >>> "Item added successfully" in html
  True
  >>> save_daniel is storage['Daniel']
  False
  >>> log.pop().object is storage['Daniel']
  True

Let's implement a class that prevents this:

  >>> class MyCarefulForm(MyForm):
  ...     def add(self, data):
  ...         name = data['name']
  ...         if name not in storage:
  ...             return super(MyCarefulForm, self).add(data)
  ...         else:
  ...             raise schema.ValidationError(
  ...                 u"There's already an item with the name '%s'" % name)

  >>> save_daniel = storage['Daniel']
  >>> html = MyCarefulForm(None, request)()
  >>> "Item added successfully" in html
  False
  >>> "There's already an item with the name 'Daniel'" in html
  True
  >>> save_daniel is storage['Daniel']
  True
  >>> len(log) == 0
  True

Render some of the fields in view mode
--------------------------------------

We can implement in our form a ``view_schema`` attribute, which will
then be used to view information in our form's table.  Let's say we
wanted the name of our persons to be viewable only in the table:

  >>> from z3c.form import field
  >>> class MyAdvancedForm(MyForm):
  ...     update_schema = field.Fields(IPerson).select('age')
  ...     view_schema = field.Fields(IPerson).select('name')
  ...     add_schema = IPerson

  >>> print MyAdvancedForm(None, TestRequest())() \
  ... # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
  <div class="crud-form">...Daniel...Maria...</div>

We can still edit the age of our Persons:

  >>> request = TestRequest()
  >>> request.form['crud-edit.Maria.widgets.age'] = u'40'
  >>> request.form['crud-edit.Daniel.widgets.age'] = u'35'
  >>> request.form['crud-edit.form.buttons.edit'] = u'Apply Changes'
  >>> html = MyAdvancedForm(None, request)()
  >>> "Successfully updated" in html
  True

  >>> storage['Maria'].age
  40
  >>> storage['Daniel'].age
  35

We can still add a Person using both name and age:

  >>> request = TestRequest()
  >>> request.form['crud-add.form.widgets.name'] = u'Thomas'
  >>> request.form['crud-add.form.widgets.age'] = u'28'
  >>> request.form['crud-add.form.buttons.add'] = u'Add'
  >>> html = MyAdvancedForm(None, request)()
  >>> "Item added successfully" in html
  True
  >>> len(storage)
  3
  >>> storage['Thomas']
  <Person with name=u'Thomas', age=28>

Our form can also contain links to our items:

  >>> class MyAdvancedLinkingForm(MyAdvancedForm):
  ...     def link(self, item, field):
  ...         if field == 'name':
  ...             return 'http://en.wikipedia.org/wiki/%s' % item.name

  >>> print MyAdvancedLinkingForm(None, TestRequest())() \
  ... # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
  <div class="crud-form">...
  ...<a href="http://en.wikipedia.org/wiki/Daniel"...
  ...<a href="http://en.wikipedia.org/wiki/Maria"...
  ...<a href="http://en.wikipedia.org/wiki/Thomas"...
  </div>

What if we wanted the name to be both used for linking to the item
*and* for edit?  We can just include the title field twice:

  >>> class MyAdvancedLinkingForm(MyAdvancedLinkingForm):
  ...     update_schema = IPerson
  ...     view_schema = field.Fields(IPerson).select('name')
  ...     add_schema = IPerson

  >>> print MyAdvancedLinkingForm(None, TestRequest())() \
  ... # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
  <div class="crud-form">...
  ...<a href="http://en.wikipedia.org/wiki/Thomas"...Thomas...</a>...
  </div>

We can now change Thomas's name and see the change reflected in the
Wikipedia link immediately:

  >>> request = TestRequest()
  >>> for name in 'Daniel', 'Maria', 'Thomas':
  ...     request.form['crud-edit.%s.widgets.name' % name] = unicode(storage[name].name)
  ...     request.form['crud-edit.%s.widgets.age' % name] = unicode(storage[name].age)
  >>> request.form['crud-edit.Thomas.widgets.name'] = u'Dracula'
  >>> request.form['crud-edit.form.buttons.edit'] = u'Apply Changes'

  >>> print MyAdvancedLinkingForm(None, request)() \
  ... # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
  <div class="crud-form">...
  ...<a href="http://en.wikipedia.org/wiki/Dracula"...Dracula...</a>...
  </div>
  >>> storage['Thomas'].name = u'Thomas'

Don't render one part
---------------------

What if we wanted our form to display only one part, that is, only the
add *or* the edit form.  Our CrudForm can implement
``editform_factory`` and ``addform_factory`` to override one or both
forms.  Seeting one of these to ``crud.NullForm`` will make them
disappear:

  >>> class OnlyEditForm(MyForm):
  ...     addform_factory = crud.NullForm
  >>> html = OnlyEditForm(None, TestRequest())()
  >>> 'Edit' in html, 'Add' in html
  (True, False)

  >>> class OnlyAddForm(MyForm):
  ...     editform_factory = crud.NullForm
  >>> html = OnlyAddForm(None, TestRequest())()
  >>> 'Edit' in html, 'Add' in html
  (False, True)

Render only in view, and define own actions
-------------------------------------------

Sometimes you want to present a list of items, possibly in view mode
only, and have the user select one or more of the items to perform
some action with them.  We'll present a minimal example that does this
here.

We can simply leave the ``update_schema`` class attribute out (it
defaults to ``None``).  Furthermore, we'll need to override the
ediform_factory with our custom version that provides other buttons
than the 'edit' and 'delete' ones:

  >>> from pprint import pprint
  >>> from z3c.form import button

  >>> class MyEditForm(crud.EditForm):
  ...     @button.buttonAndHandler(u'Capitalize', name='capitalize')
  ...     def handle_capitalize(self, action):
  ...         self.status = u"Please select items to capitalize first."
  ...         selected = self.selected_items()
  ...         if selected:
  ...             self.status = u"Capitalized items"
  ...             for id, item in selected:
  ...                 item.name = item.name.upper()

  >>> class MyCustomForm(crud.CrudForm):
  ...     view_schema = IPerson
  ...     editform_factory = MyEditForm
  ...     addform_factory = crud.NullForm     # We don't want an add part.
  ... 
  ...     def get_items(self):
  ...         return sorted(storage.items(), key=lambda x: x[1].name)

  >>> request = TestRequest()
  >>> html = MyCustomForm(None, TestRequest())()
  >>> "Delete" in html, "Apply changes" in html, "Capitalize" in html
  (False, False, True)
  >>> pprint(storage)
  {'Daniel': <Person with name=u'Daniel', age=35>,
   'Maria': <Person with name=u'Maria', age=40>,
   'Thomas': <Person with name=u'Thomas', age=28>}

  >>> request.form['crud-edit.Thomas.widgets.select'] = ['selected']
  >>> request.form['crud-edit.form.buttons.capitalize'] = u'Capitalize'
  >>> html = MyCustomForm(None, request)()
  >>> "Capitalized items" in html
  True
  >>> pprint(storage)
  {'Daniel': <Person with name=u'Daniel', age=35>,
   'Maria': <Person with name=u'Maria', age=40>,
   'Thomas': <Person with name=u'THOMAS', age=28>}

We *cannot* use any of the other buttons:

  >>> del request.form['crud-edit.form.buttons.capitalize']
  >>> request.form['crud-edit.form.buttons.delete'] = u'Delete'
  >>> html = MyCustomForm(None, request)()
  >>> "Successfully deleted items" in html
  False
  >>> 'Thomas' in storage
  True

Customizing sub forms
---------------------

The EditForm class allows you to specify an editsubform_factory-a classs 
inherits from EditSubForm.  This allows you to say, override the crud-row.pt
page template and customize the look of the fields.

  >>> import zope.schema
  >>> class MyCustomEditSubForm(crud.EditSubForm):
  ...
  ...     def _select_field(self):
  ...         """I want to customize the field that it comes with..."""
  ...         select_field = field.Field(
  ...         zope.schema.TextLine(__name__='select',
  ...                              required=False,
  ...                              title=u'select'))
  ...         return select_field

  >>> class MyCustomEditForm(MyEditForm):
  ...     editsubform_factory = MyCustomEditSubForm

  >>> class MyCustomFormWithCustomSubForm(MyCustomForm):
  ...     editform_factory = MyCustomEditForm

  >>> request = TestRequest()
  >>> html = MyCustomFormWithCustomSubForm(None, TestRequest())()

Still uses same form as before
  >>> "Delete" in html, "Apply changes" in html, "Capitalize" in html
  (False, False, True)

Just changes the widget used for selecting...
  >>> 'type="checkbox"' in html
  False

Using batching
--------------

The CrudForm base class supports batching.  When setting the
``batch_size`` attribute to a value greater than ``0``, we'll only get
as many items displayed per page.

  >>> class MyBatchingForm(MyForm):
  ...     batch_size = 2
  >>> request = TestRequest()
  >>> html = MyBatchingForm(None, request)()
  >>> "Daniel" in html, "Maria" in html
  (True, True)
  >>> "THOMAS" in html
  False

  >>> request.form['crud-edit.form.page'] = '1'
  >>> html = MyBatchingForm(None, request)()
  >>> "Daniel" in html, "Maria" in html
  (False, False)
  >>> "THOMAS" in html
  True

Let's change Thomas' age on the second page:

  >>> request.form['crud-edit.Thomas.widgets.name'] = u'Thomas'
  >>> request.form['crud-edit.Thomas.widgets.age'] = '911'
  >>> request.form['crud-edit.form.buttons.edit'] = u'Apply changes'
  >>> html = MyBatchingForm(None, request)()
  >>> "Successfully updated" in html
  True
  >>> "911" in html
  True
