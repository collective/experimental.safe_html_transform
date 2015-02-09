    
===================
 wicked.fieldevent
===================

a little while back, ben recommended a pattern for rendering and
storage of field data that that used events to retrieve and store
values. this is a implementation of that idea.

fundamentals
============

Here is a rudimentary field example with all the other at cruft
stripped away except for a standard get and set. For the purposes of
this demonstration, the value is stored on the field, but
could be anywhere.

    >>> from zope.interface import implements, Interface, alsoProvides
    >>> class IPage(Interface):
    ...     """ I'm a page """

    >>> class IBodyField(IField):
    ...     """ I'm the main content """

    >>> class Content(object):
    ...     implements(IPage)
    ...     """ a bag """

    >>> class MockField(object):
    ...     implements(IBodyField)
    ...     value=None
    ...     
    ...     def get(self, instance, **kw):
    ...         return self.value
    ...     
    ...     def set(self, instance, value, **kw):
    ...         self.value = value

    >>> field1 = MockField()
    >>> content1 = Content()

These convenience methods do all the lifting::

    >>> store(field1, content1, "HELLO", **dict(foo='bar'))
    >>> print render(field1, content1, **dict(foo='bar'))
    HELLO

Let's consider something a bit fancier. wicked.fieldevent comes with a
filtration handler(remember filter and txtfilter?). We'll start by
registering the handler to some discrete interfaces::

    >>> from txtfilter import txtfilter_output, ITxtFilter, ITxtFilterList 
    >>> provideHandler(txtfilter_output,
    ...                adapts=[IBodyField, IPage, IFieldRenderEvent])

Using a closure we cam define a simple callable txtfilter(and register
it)::

    >>> @implementer(ITxtFilter)
    ... @adapter(IBodyField, IPage, IFieldRenderEvent) 
    ... def kimjongil(field, context, event):
    ...     def txtfilter():
    ...         event.value = event.value.replace('l', 'r')
    ...         event.value = event.value.replace('L', 'R')
    ...     txtfilter.name = kimjongil.__name__
    ...     return txtfilter
    >>> provideSubscriptionAdapter(kimjongil)

Initially, nothing with happen(we haven't configured a filter list)::

    >>> text = "Hello, my name is kim jong il. I love nuclear weapons"
    >>> store(field1, content1, text, **dict(foo='bar'))
    >>> print render(field1, content1, **dict(foo='bar'))
    Hello, my name is kim jong il. I love nuclear weapons

so we'll set up a hook to load with filter names::

    >>> _filter_list = [kimjongil.__name__]
    >>> @implementer(ITxtFilterList)
    ... @adapter(IBodyField, IPage, IFieldRenderEvent) 
    ... def filter_list(*args):
    ...     return _filter_list
    >>> provideAdapter(filter_list)
    >>> print render(field1, content1, **dict(foo='bar'))
    Herro, my name is kim jong ir. I rove nucrear weapons

we can also extend the abstract base class provided::

    >>> import re
    >>> from txtfilter import TxtFilter
    >>> class WimpyWiki(TxtFilter):
    ...     adapts(IBodyField, IPage, IFieldRenderEvent)
    ...     
    ...     pattern=re.compile(r'([A-Z][a-z]+[A-Z]\w+)')
    ...     
    ...     def _filterCore(self, chunk, **kw):
    ...         return '<a class="addlink">%s</a>' %chunk

    >>> WimpyWiki.name = WimpyWiki.__name__
    >>> provideSubscriptionAdapter(WimpyWiki)
    >>> _filter_list.append(WimpyWiki.name)

now rendering will execute both filters::

    >>> text = "TeamAmerica: freedom isn't free.\nLivinLaVidaDPRK by kim jong il"
    >>> store(field1, content1, text, **dict(foo='bar'))
    >>> print render(field1, content1, **dict(foo='bar'))
    <a class="addlink">TeamAmerica</a>: freedom isn't free.
    <a class="addlink">RivinRaVidaDPRK</a> by kim jong ir

lastly, a filter raising an EndFiltrationException can stop
filtering. This filter also demonstrates a switching concept using
event.kwargs.  AT field pass around the schema in kwargs and other bad
stuff that can come in handy::

    >>> from interfaces import EndFiltrationException
    >>> @implementer(ITxtFilter)
    ... @adapter(IBodyField, IPage, IFieldRenderEvent) 
    ... def censor(field, context, event):
    ...     def txtfilter():
    ...         """if censoring, blank all but last 2 chars"""
    ...         if event.kwargs.get('censor', None):
    ...             event.value="CENSORED:%s" %event.value[-2:]
    ...             raise EndFiltrationException
    ...     txtfilter.name = censor.__name__
    ...     return txtfilter
    >>> provideSubscriptionAdapter(censor)
    >>> _filter_list.insert(1, censor.__name__)

Rendering as before acts normally::

    >>> print render(field1, content1, **dict(foo='bar'))
    <a class="addlink">TeamAmerica</a>: freedom isn't free.
    <a class="addlink">RivinRaVidaDPRK</a> by kim jong ir

Pass a keyword trigger, and the first two text transformation occur,
but not the wimpy wiki.

    >>> print render(field1, content1, **dict(censor=True))
    CENSORED:ir
