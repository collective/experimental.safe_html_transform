zope.globalrequest
==================

Introduction
------------

This package provides a global way to retrieve the currently active request
object in a zope-based web framework.  To do so you simply need to do the
following::

  from zope.globalrequest import getRequest
  request = getRequest()

This package is mainly intended to be used with the Zope2/Plone stack.  While
it also works with the Zope3 framework, the latter promotes a clean separation
of concerns and the pattern of having a globally available request object is
discouraged.


Functional Tests
----------------

The remainder of this file contains functional tests to demonstrate that the
package works as intended.

First we need to define a browser view along with an interface for a utility
that will be used by that view:

  >>> from zope.interface import Interface
  >>> class IFoo(Interface):
  ...     """ interface for a foo-ish utility """
  ...     def foo():
  ...         """ return some foo """

  >>> from zope.publisher.browser import BrowserPage
  >>> from zope.component import queryUtility
  >>> class FooView(BrowserPage):
  ...    """ a browser view """
  ...    def __call__(self, *args, **kw):
  ...        foo = queryUtility(IFoo, default=None)
  ...        if foo is not None:
  ...            return foo.foo()
  ...        else:
  ...            return 'sif!'

Unfortunately the view class cannot be directly imported from here, i.e.
relatively, so we have to make it available from somewhere else in order to register it:

  >>> from zope.globalrequest import tests
  >>> tests.FooView = FooView
  >>> zcml("""
  ... <configure
  ...     xmlns="http://namespaces.zope.org/zope"
  ...     xmlns:browser="http://namespaces.zope.org/browser">
  ...   <include package="zope.app.publisher" file="meta.zcml" />
  ...   <browser:page
  ...     name="foo"
  ...     for="*"
  ...     class="zope.globalrequest.tests.FooView"
  ...     permission="zope.Public" />
  ... </configure>
  ... """)

Next let's make sure our test view actually works:

  >>> from zope.testbrowser.testing import Browser
  >>> browser = Browser()
  >>> browser.open('http://localhost/@@foo')
  >>> browser.contents
  'sif!'

The view tries to query for a utility and use it to "calculate" it's response,
so let's define one:

  >>> from zope.interface import implements
  >>> from zope.globalrequest import getRequest
  >>> class Foo(object):
  ...     implements(IFoo)
  ...     def foo(self):
  ...         request = getRequest()
  ...         if request:
  ...             name = request.get('name', 'n00b')
  ...         else:
  ...             name = 'foo'
  ...         return 'y0 %s!' % name

Again, the utility class and interface cannot be directly imported from here,
so let's also make them available from somewhere else in order to register
utility:

  >>> tests.Foo = Foo
  >>> tests.IFoo = IFoo
  >>> zcml("""
  ... <configure xmlns="http://namespaces.zope.org/zope">
  ...   <include package="zope.component" file="meta.zcml" />
  ...   <utility
  ...     factory="zope.globalrequest.tests.Foo"
  ...     provides="zope.globalrequest.tests.IFoo" />
  ... </configure>
  ... """)

Rendering the view again should now give us the default value provided by the
utility:

  >>> browser.reload()
  >>> browser.contents
  'y0 foo!'

Up to now the request hasn't been stored for us yet, so let's hook up the
necessary event subscribers and try that again:

  >>> zcml("""
  ... <configure xmlns="http://namespaces.zope.org/zope">
  ...   <include package="zope.component" file="meta.zcml" />
  ...   <include package="zope.globalrequest" />
  ... </configure>
  ... """)

Now we should get the request and therefore the fallback value from the form
lookup:

  >>> browser.reload()
  >>> browser.contents
  'y0 n00b!'

If we now provide a request value we should be greeted properly:

  >>> browser.open('?name=d4wg!')
  >>> browser.contents
  'y0 d4wg!!'

Once the request has been processed, it should not be available anymore:

  >>> print getRequest()
  None

