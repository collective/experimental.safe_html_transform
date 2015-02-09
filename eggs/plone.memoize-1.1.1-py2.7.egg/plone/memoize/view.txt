=====================
 view memo decorators
=====================

Decorators for methods/properties in views. Values are cached by annotating
the view's request, and keyed based on the context and any arguments to the
function. This means that the same view can be looked up multiple times and
the same memos will be returned::

>>> from plone.memoize import view
>>> from zope.component import adapts
>>> from zope.interface import implements
>>> from zope.interface import Interface
>>> from zope.publisher.interfaces.browser import IBrowserRequest
>>> from zope.publisher.interfaces.browser import IBrowserView

First we set up a dummy view::

>>> class MyView(object):
...     implements(IBrowserView)
...     adapts(Interface, IBrowserRequest)
...
...     def __init__(self, context, request):
...         self.context = context
...         self.request = request
...
...     txt1 = 'hello'
...     bang = '!'
...
...     @property
...     @view.memoize
...     def txt2(self):
...         return '%s world' % self.txt1
...
...     @view.memoize
...     def getMsg(self, to, **instruction):
...         lst = ['%s--%s' %t for t in instruction.items()]
...         instxt = ' '.join(lst)
...         return ("%s: %s world%s %s" %(to, self.txt1, self.bang, instxt)).strip()
...
...     @view.memoize_contextless
...     def getAnotherMsg(self, to, **instruction):
...         lst = ['%s--%s' %t for t in instruction.items()]
...         instxt = ' '.join(lst)
...         return ("%s: %s world%s %s" %(to, self.txt1, self.bang, instxt)).strip()
...

>>> from zope.component import provideAdapter
>>> provideAdapter(MyView, name=u'msg_view')

We also need a dummy context::

>>> class Dummy(object):
...     implements(Interface)

Let's look up the view:

>>> from zope.publisher.browser import TestRequest
>>> request = TestRequest()
>>> context = Dummy()

We need request to be annotatable::

>>> from zope.interface import directlyProvides
>>> from zope.annotation.interfaces import IAttributeAnnotatable
>>> directlyProvides(request, IAttributeAnnotatable)

>>> from zope.component import getMultiAdapter
>>> msg = getMultiAdapter((context, request), name=u'msg_view')

Now, if we access the memoized property txt2, we will get the value in 
txt1::

>>> msg.txt2
'hello world'

>>> msg.txt1 = 'goodbye cruel'

Even though we've twiddled txt1, txt2 is not recalculated::

>>> msg.txt2
'hello world'

We support memoization of multiple signatures as long as all
signature values are hashable::

>>> print msg.getMsg('Ernest')
Ernest: goodbye cruel world!

>>> print msg.getMsg('J.D.', **{'raise':'roofbeams'})
J.D.: goodbye cruel world! raise--roofbeams

We can alter data underneath, but nothing changes::

>>> msg.txt1 = 'sound and fury'
>>> print msg.getMsg('J.D.', **{'raise':'roofbeams'})
J.D.: goodbye cruel world! raise--roofbeams

>>> print msg.getMsg('Ernest')
Ernest: goodbye cruel world!

If we alter the signature, our msg is recalculated:

>>> ins = {'tale':'told by idiot', 'signify':'nothing'}
>>> print msg.getMsg('Bill F.', **ins)
Bill F.: sound and fury world! tale--told by idiot signify--nothing

>>> print msg.getMsg('J.D.', **{'catcher':'rye'})
J.D.: sound and fury world! catcher--rye

If change the bang, the memo remains the same::

>>> msg.bang='#!'
>>> print msg.getMsg('J.D.', **{'catcher':'rye'})
J.D.: sound and fury world! catcher--rye

>>> print msg.getMsg('Ernest')
Ernest: goodbye cruel world!

If we look up the view again on the same object, we will get the same 
memoized properties as before:

>>> msg2 = getMultiAdapter((context, request), name=u'msg_view')

>>> msg2.txt1 = 'and so on'
>>> msg2.bang = '&'

>>> msg2.txt2
'hello world'

>>> print msg2.getMsg('J.D.', **{'raise':'roofbeams'})
J.D.: goodbye cruel world! raise--roofbeams

>>> print msg2.getMsg('Ernest')
Ernest: goodbye cruel world!

>>> ins = {'tale':'told by idiot', 'signify':'nothing'}
>>> print msg2.getMsg('Bill F.', **ins)
Bill F.: sound and fury world! tale--told by idiot signify--nothing

>>> print msg2.getMsg('J.D.', **{'catcher':'rye'})
J.D.: sound and fury world! catcher--rye

However, if we look up the view on another context object, things change:

>>> context = Dummy()
>>> msg3 = getMultiAdapter((context, request), name=u'msg_view')

>>> msg3.txt1 = 'so long, cruel'
>>> msg3.bang = '&'

>>> msg3.txt2
'so long, cruel world'

>>> print msg3.getMsg('J.D.', **{'raise':'roofbeams'})
J.D.: so long, cruel world& raise--roofbeams

>>> print msg3.getMsg('Ernest')
Ernest: so long, cruel world&

>>> ins = {'tale':'told by idiot', 'signify':'nothing'}
>>> print msg3.getMsg('Bill F.', **ins)
Bill F.: so long, cruel world& tale--told by idiot signify--nothing

>>> print msg3.getMsg('J.D.', **{'catcher':'rye'})
J.D.: so long, cruel world& catcher--rye

This behaviour does not apply to contextless decorators, which memoize
based on parameters, but not on context:

>>> print msg3.getAnotherMsg('J.D.', **{'raise':'roofbeams'})
J.D.: so long, cruel world& raise--roofbeams

>>> print msg2.getAnotherMsg('J.D.', **{'raise':'roofbeams'})
J.D.: so long, cruel world& raise--roofbeams
