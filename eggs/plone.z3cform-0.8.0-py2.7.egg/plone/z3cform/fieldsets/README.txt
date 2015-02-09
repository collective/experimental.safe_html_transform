Fieldsets and form extenders
============================

The ``plone.z3cform.fieldsets`` package provides support for z3c.form groups
(fieldsets) and other modifications via "extender" adapters. The idea is that
a third party component can modify the fields in the form and the way that
they are grouped and ordered.

This support relies on a mixin class, which is itself a subclass of 
z3c.form's ``GroupForm``.

    >>> from plone.z3cform.fieldsets import group, extensible

To use this, you have to mix it into another form as the *first* base class:

  >>> from zope.annotation import IAttributeAnnotatable
  >>> from z3c.form import form, field, tests, group
  >>> from zope.interface import Interface, implements
  >>> from zope import schema

  >>> class ITest(Interface):
  ...     title = schema.TextLine(title=u"Title")

  >>> class Test(object):
  ...     # avoid needing an acl_users for this test in Zope 2.10
  ...     __allow_access_to_unprotected_subobjects__ = 1
  ...     implements(ITest, IAttributeAnnotatable)
  ...     title = u""
  ...     def getPhysicalRoot(self): # needed for template to acquire REQUEST in Zope 2.10
  ...         return self

  >>> class TestForm(extensible.ExtensibleForm, form.Form):
  ...     fields = field.Fields(ITest)

Here, note the order of the base classes. Also note that we use an ordinary
set of fields directly on the form. This known as the default fieldset.

This form should work as-is, i.e. we can update it. First we need to fake a
request.

  >>> from plone.z3cform.tests import TestRequest

  >>> request = TestRequest()
  >>> request.other = {}
  >>> context = Test()
  >>> context.REQUEST = request

  >>> form = TestForm(context, request)
  >>> try: # Zope 2.10 templates need a proper acquisition chain
  ...     from Acquisition import ImplicitAcquisitionWrapper
  ...     form = ImplicitAcquisitionWrapper(form, context)
  ... except:
  ...     pass
  >>> form.update()
  >>> _ = form.render()

Now let's register an adapter that adds two new fields - one in the
default fieldset as the first field, and one in a new group. To do this,
we only need to register a named multi-adapter. However, we can use a 
convenience base class to make it easier to manipulate the fields of the
form.

  >>> from plone.z3cform.fieldsets.interfaces import IFormExtender
  >>> from zope.component import adapts, provideAdapter
  
  >>> class IExtraBehavior(Interface):
  ...     foo = schema.TextLine(title=u"Foo")
  ...     bar = schema.TextLine(title=u"Bar")
  ...     baz = schema.TextLine(title=u"Baz")
  ...     fub = schema.TextLine(title=u"Fub")
  ...     qux = schema.TextLine(title=u"Qux")
  
One plausible implementation is to use an annotation to store this data.

  >>> from zope.annotation import factory
  >>> from zope.annotation.attribute import AttributeAnnotations
  >>> from persistent import Persistent
  >>> class ExtraBehavior(Persistent):
  ...     implements(IExtraBehavior)
  ...     adapts(Test)
  ...     
  ...     foo = u""
  ...     bar = u""
  ...     baz = u""
  ...     fub = u""
  ...     qux = u""
  
  >>> ExtraBehavior = factory(ExtraBehavior)
  >>> provideAdapter(ExtraBehavior)
  >>> provideAdapter(AttributeAnnotations)
 
We can now write the extender. The base class gives us some helper methods
to add, remove and move fields. Here, we do a bit of unnecessary work just
to exercise these methods.
 
  >>> class ExtraBehaviorExtender(extensible.FormExtender):
  ...     adapts(Test, TestRequest, TestForm) # context, request, form
  ...
  ...     def __init__(self, context, request, form):
  ...         self.context = context
  ...         self.request = request
  ...         self.form = form
  ...     
  ...     def update(self):
  ...         # Add all fields from an interface
  ...         self.add(IExtraBehavior, prefix="extra")
  ...         
  ...         # Remove the fub field
  ...         self.remove('fub', prefix="extra")
  ...         
  ...         all_fields = field.Fields(IExtraBehavior, prefix="extra")
  ...         
  ...         # Insert fub again, this time at the top
  ...         self.add(all_fields.select("fub", prefix="extra"), index=0)
  ...         
  ...         # Move 'baz' above 'fub'
  ...         self.move('baz', before='fub', prefix='extra', relative_prefix='extra')
  ...         
  ...         # Move 'foo' after 'bar' - here we specify prefix manually
  ...         self.move('foo', after='extra.bar', prefix='extra')
  ...         
  ...         # Remove 'bar' and re-insert into a new group
  ...         self.remove('bar', prefix='extra')
  ...         self.add(all_fields.select('bar', prefix='extra'), group='Second')
  ...         
  ...         # Move 'baz' after 'bar'. This means it also moves group.
  ...         self.move('extra.baz', after='extra.bar')
  ...         
  ...         # Remove 'qux' and re-insert into 'Second' group,
  ...         # then move it before 'baz'
  ...         self.remove('qux', prefix='extra')
  ...         self.add(all_fields.select('qux', prefix='extra'), group='Second')
  ...         self.move('qux', before='baz', prefix='extra', relative_prefix='extra')
  
  >>> provideAdapter(factory=ExtraBehaviorExtender, name=u"test.extender")
    
With this in place, let's update the form once again.

  >>> form = TestForm(context, request)
  >>> form.update()

At this point, we should have a set of default fields that represent the
ones set in the adapter.

  >>> form.fields.keys()
  ['extra.fub', 'title', 'extra.foo']
  
And we should have one group created by the group factory:

  >>> form.groups # doctest: +ELLIPSIS
  (<plone.z3cform.fieldsets.group.Group object at ...>,)

Note that the created group is of a subtype of the standard z3c.form group,
which has got support for a separate label and description as well as a 
canonical name.

  >>> isinstance(form.groups[0], group.Group)
  True

This should have the group fields provided by the adapter as well.

  >>> form.groups[0].fields.keys()
  ['extra.bar', 'extra.qux', 'extra.baz']
