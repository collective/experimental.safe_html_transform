Writing indexers
================

An indexer is a named adapter that adapts the type of an object and provides
a value to be indexed when the catalog attempts to index the attribute with
that name.

For example, let's say we have two types, page and news item:

    >>> from zope.interface import implements, Interface
    >>> from zope import schema

    >>> class IPage(Interface):
    ...     text = schema.Text(title=u"Body text")
    >>> class Page(object):
    ...     implements(IPage)
    ...     def __init__(self, text):
    ...         self.text = text

    >>> class INewsItem(Interface):
    ...     summary = schema.TextLine(title=u"Short summary")
    ...     story = schema.Text(title=u"Body text")
    ...     audience = schema.TextLine(title=u"Audience")

    >>> class NewsItem(object):
    ...     implements(INewsItem)
    ...     def __init__(self, summary, story, audience):
    ...         self.summary = summary
    ...         self.story = story
    ...         self.audience = audience

Now, pretend that our catalog had an index 'description', which for a page
should contain the first 10 characters from the body text, and for a news
item should contain the contents of the 'summary' field. Furthermore, there
is an index 'audience' that should contain the value of the corresponding
field for news items, in all uppercase. It should do nothing for pages.

We could write indexers for all of these like this

    >>> from plone.indexer import indexer
    
    >>> @indexer(IPage)
    ... def page_description(object):
    ...     return object.text[:10]

    >>> @indexer(INewsItem)
    ... def newsitem_description(object):
    ...     return object.summary

    >>> @indexer(INewsItem)
    ... def newsitem_audience(object):
    ...     return object.audience.upper()

These need to be registered as named adapters, where the name corresponds to
the index name. In ZCML, that may be::

    <adapter name="description" factory=".indexers.page_description" />
    <adapter name="description" factory=".indexers.newsitem_description" />
    <adapter name="audience" factory=".indexers.newsitem_audience" />

We can omit the 'for' attribute because we passed this to the @indexer
decorator, and we can omit the 'provides' attribute because the thing 
returned by the decorator is actually a class providing the required IIndexer
interface.

For the purposes of the ensuing tests, we'll register these directly.

    >>> from zope.component import provideAdapter
    >>> provideAdapter(page_description, name='description')
    >>> provideAdapter(newsitem_description, name='description')
    >>> provideAdapter(newsitem_audience, name='audience')

Testing your indexers (or calling them directly)
------------------------------------------------

If you are writing tests for your indexers (as you should!), then you should
be aware of the following:

When the @indexer decorator returns, it turns your function into an instance
of type DelegatingIndexerFactory. This is an adapter factory that can create
a DelegatingIndexer, which in turn will call your function when asked to
perform indexing operations.
   
This means that you can't just call your function to test the indexer.
Instead, you need to instantiate the adapter and then call the delegating
indexer with the portal root as the first argument. For example:
 
    >>> test_page = Page(text=u"My page with some text")
    >>> page_description(test_page)()
    u'My page wi'

This will suffice in most cases. Note that there is actually a second
parameter, catalog, which defaults to None. If you need to write an indexer
that acts on catalog, you'll need to register a conventional adapter, as
described in the next section.

Other means of registering indexers
-----------------------------------

At the end of the day, an indexer is just a named multi-adapter from the
indexable object (e.g. INewsItem or IPage above) and the catalog (usually
portal_catalog in a CMF application) to IIndexer, where the name is the name
of the indexed attribute in the catalog. Thus, you could register your
indexers as more conventional adapters:

    >>> from plone.indexer.interfaces import IIndexer
    >>> from Products.ZCatalog.interfaces import IZCatalog

    >>> from zope.interface import implements
    >>> from zope.component import adapts
    >>> class LengthIndexer(object):
    ...     """Index the length of the body text
    ...     """
    ...     implements(IIndexer)
    ...     adapts(IPage, IZCatalog)
    ...     
    ...     def __init__(self, context, catalog):
    ...         self.context = context
    ...         self.catalog = catalog
    ...         
    ...     def __call__(self):
    ...         return len(self.context.text)

We normally just use IZCatalog for the catalog adaptation, to apply to any
catalog. However, if you want different indexers for different types of
catalogs, there is an example later in this test.

You'd register this with ZCML like so::

    <adapter factory=".indexers.LengthIndexer" name="length" />
    
Or in a test:

    >>> provideAdapter(LengthIndexer, name="length")

If you're only curious about how to write indexers, you can probably stop
here. If you want to know more about how they work and how they are wired into
a framework, read on.

Hooking up indexers to the framework
=====================================

Here is a mock implementation of a ZCatalog.catalog_object() override, based
on the one in Plone. We'll use this for testing. We won't bother with the full
ZCatalog interface, only catalog_object(), and we'll stub out a few things.
This really is for illustration purposes only, to show the intended usage
pattern.

In CMF 2.2, there is an IIndexableObject marker interface defined in 
Products.CMFCore.interfaces. We have a compatibility alias in this package
for use with CMF 2.1.

    >>> from OFS.interfaces import IItem
    >>> from Products.ZCatalog.interfaces import IZCatalog
    >>> from plone.indexer.interfaces import IIndexableObject
    >>> from zope.component import queryMultiAdapter

    >>> class FauxCatalog(object):
    ...     implements(IZCatalog, IItem)
    ...
    ...     def catalog_object(self, object, uid, idxs=[]):
    ...         """Pretend to index 'object' under the key 'uid'. We'll
    ...         print the results of the indexing operation to the screen .
    ...         """
    ...         
    ...         if not IIndexableObject.providedBy(object):
    ...             wrapper = queryMultiAdapter((object, self,), IIndexableObject)
    ...             if wrapper is not None:
    ...                 object = wrapper
    ...         
    ...         # Perform the actual indexing of attributes in the idxs list
    ...         for idx in idxs:
    ...             try:
    ...                 indexed_value = getattr(object, idx)
    ...                 if callable(indexed_value):
    ...                     indexed_value = indexed_value()
    ...                 print idx, "=", indexed_value
    ...             except (AttributeError, TypeError,):
    ...                 pass

The important things here are:

    - We attempt to obtain an IIndexableObject for the object to be indexed.
      This is just a way to get hold of an implementation of this interface
      (we'll register one in a moment) and allow some coarse-grained overrides.
      
    - Cataloging involves looking up attributes on the indexable object 
      wrapper matching the names of indexes (in the real ZCatalog, this is
      actually decoupled, but let's not get carried away). If they are
      callable, they should be called. This is just mimicking what ZCatalog's
      implementation does.
      
This package comes with an implementation of an IIndexableObject adapter that
knows how to delegate to an IIndexer. Let's now register that as the default
IIndexableObject wrapper adapter so that the code above will find it.

    >>> from plone.indexer.wrapper import IndexableObjectWrapper
    >>> from plone.indexer.interfaces import IIndexableObject
    >>> provideAdapter(factory=IndexableObjectWrapper, adapts=(Interface, IZCatalog,), provides=IIndexableObject)

Seeing it in action
===================

Now for the testing. First, we need a faux catalog:

    >>> catalog = FauxCatalog()

Finally, let's create some objects to index.

    >>> page = Page(u"The page body text here")
    >>> news = NewsItem(u"News summary", u"News body text", u"Audience")

First of all, let's demonstrate that our indexers work and apply only to
the types for which they are registered.

    >>> catalog.catalog_object(page, 'p1', idxs=['description', 'audience', 'length'])
    description = The page b
    length = 23

    >>> catalog.catalog_object(news, 'n1', idxs=['description', 'audience', 'length'])
    description = News summary
    audience = AUDIENCE

Our custom indexable object wrapper is capable of looking up workflow
variables if the portal_workflow tool is available. For testing purposes,
we'll create a fake minimal workflow tool and stash it onto the fake catalog
so that it can be found by getToolByName. In real life, it would of course be
acquirable as normal.

    >>> class FauxWorkflowTool(object):
    ...     implements(IItem)
    ...     def getCatalogVariablesFor(self, object):
    ...         return dict(review_state='published', audience='Somebody')
    >>> catalog.portal_workflow = FauxWorkflowTool()

If we now index 'review_state', it will be obtained from the workflow
variables. However, a custom indexer still overrides workflow variables.

    >>> catalog.catalog_object(news, 'n1', idxs=['description', 'audience', 'review_state'])
    description = News summary
    audience = AUDIENCE
    review_state = published

Finally, if not adapter can be found, we fall back on getattr() on the object.

    >>> catalog.catalog_object(page, 'p3', idxs=['description', 'text'])
    description = The page b
    text = The page body text here

Customising indexers based on the catalog type
==============================================

It is possible to provide a custom indexer for a different type of catalog.
To test that, let's create a secondary catalog and mark it with a marker
interface.

    >>> from zope.interface import Interface
    >>> class IAlternateCatalog(Interface):
    ...     pass
    >>> from zope.interface import alsoProvides
    >>> catalog2 = FauxCatalog()
    >>> alsoProvides(catalog2, IAlternateCatalog)

Let's say that we did not want the news item audience uppercased here. We
could provide a custom indexer for just this catalog:

    >>> @indexer(INewsItem, IAlternateCatalog)
    ... def alternate_newsitem_audience(object):
    ...     return object.audience.lower()
    >>> provideAdapter(alternate_newsitem_audience, name='audience')

This does not affect the first catalog:

    >>> catalog.catalog_object(news, 'n1', idxs=['description', 'audience', 'length'])
    description = News summary
    audience = AUDIENCE

However, the second catalog gets the audience in lowercase.

    >>> catalog2.catalog_object(news, 'n1', idxs=['description', 'audience', 'length'])
    description = News summary
    audience = audience

Interfaces provided by the wrapper
==================================

The indexable object wrapper has one particular feature: instances of the
wrapper will provide the same interfaces as instances of the wrapped object.
For example:

    >>> from plone.indexer.interfaces import IIndexableObjectWrapper, IIndexableObject
    >>> wrapper = IndexableObjectWrapper(page, catalog)
    >>> IIndexableObjectWrapper.providedBy(wrapper)
    True
    >>> IIndexableObject.providedBy(wrapper)
    True
    >>> IPage.providedBy(wrapper)
    True
    >>> INewsItem.providedBy(wrapper)
    False

    >>> wrapper = IndexableObjectWrapper(news, catalog)
    >>> IIndexableObjectWrapper.providedBy(wrapper)
    True
    >>> IPage.providedBy(wrapper)
    False
    >>> INewsItem.providedBy(wrapper)
    True

Unboxing
========

It is possible to obtain the wrapped object from the wrapper:

    >>> wrapper = IndexableObjectWrapper(page, catalog)
    >>> wrapper._getWrappedObject() is page
    True
