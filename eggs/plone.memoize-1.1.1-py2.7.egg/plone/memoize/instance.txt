====================
 instance decorators
====================

Originally from Whit Morriss' memojito package, they are used to
memoize return values for methods on an instance. The memoized values
are stored on an attribute on the instance and disappear when the
instance is destroyed or a cleanup is called.

Let's try it out w/ a dummy class::

>>> from plone.memoize import instance
>>> class MyMsg(object):
...     bang='!'
...
...     @property
...     @instance.memoize
...     def txt2(self):
...         #extreme intense calculation
...         return '%s world' %self.txt1
...         
...     @instance.memoize
...     def getMsg(self, to, **instruction):
...         lst = ['%s--%s' %t for t in instruction.items()]
...         instxt = ' '.join(lst)
...         return ("%s: %s%s %s" %(to, self.txt2, self.bang, instxt)).strip()
...     
...     @instance.memoizedproperty
...     def recurse(self):
...         return "recursive: %s" % self.txt2
...
...     @instance.clearbefore
...     def clearbefore(self):
...         return self.txt2
...     
...     @instance.clearafter
...     def clearafter(self):
...         return self.txt2
...     
...     def __init__(self, txt1):
...         self.txt1 = txt1

>>> msg = MyMsg('hello')
>>> msg.txt2
'hello world'

>>> msg.txt1 = 'nice to visit this'

Even though we've twiddled txt1, txt2 is not recalculated::

>>> msg.txt2
'hello world'

The memo is stored by a key made of the method's name, args,
and a frozenset of any kwargs. If those are expected to be big,
you should compute your own hash of it.

>>> key = ('txt2', (msg,), frozenset([]))
>>> msg._memojito_[key]
'hello world'

The clear after decorator will clear the memos after
returning the methods value::

>>> msg.clearafter()
'hello world'

So now the message should have changed::

>>> msg.txt2
'nice to visit this world'

We change the text again::

>>> msg.txt1 = 'goodbye cruel'

The message is still the same of course::

>>> msg.txt2
'nice to visit this world'

Now we can test the clear before, which does the opposite from the
clear after, allowing new values to be calculated::

>>> msg.clearbefore()
'goodbye cruel world'

memojito supports memoization of multiple signatures as long as all
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

If we alter the signature, our msg is recalculated, but since mst.txt2
is a memo, only the values passed in change::

>>> ins = {'tale':'told by idiot', 'signify':'nothing'}
>>> print msg.getMsg('Bill F.', **ins)
Bill F.: goodbye cruel world! tale--told by idiot signify--nothing

>>> print msg.getMsg('J.D.', **{'catcher':'rye'})
J.D.: goodbye cruel world! catcher--rye

If change the bang, the memo remains the same::

>>> msg.bang='#!'
>>> print msg.getMsg('J.D.', **{'catcher':'rye'})
J.D.: goodbye cruel world! catcher--rye

>>> print msg.getMsg('Ernest')
Ernest: goodbye cruel world!

clearing works the same as for properties::

>>> print msg.clearafter()
goodbye cruel world

Our shebang appears::

>>> print msg.getMsg('Ernest')
Ernest: sound and fury world#!

Our message to faulkner now is semantically correct::

>>> ins = dict(tale='told by idiot', signify='nothing')
>>> print msg.getMsg('Bill F.', **ins)
Bill F.: sound and fury world#! tale--told by idiot signify--nothing

Let's make sure that memoized properties which call OTHER memoized
properties do the right thing::

>>> msg = MyMsg('hello')
>>> print msg.recurse
recursive: hello world

Now we make sure that both the txt2 and the recurse values are in the
cache::

>>> print len(msg._memojito_.keys())
2
