================
Relation Catalog
================

.. contents::
   :local:

Overview
========

The relation catalog can be used to optimize intransitive and transitive
searches for N-ary relations of finite, preset dimensions.

For example, you can index simple two-way relations, like employee to
supervisor; RDF-style triples of subject-predicate-object; and more complex
relations such as subject-predicate-object with context and state.  These
can be searched with variable definitions of transitive behavior.

The catalog can be used in the ZODB or standalone. It is a generic, relatively
policy-free tool.

It is expected to be used usually as an engine for more specialized and
constrained tools and APIs. Three such tools are zc.relationship containers,
plone.relations containers, and zc.vault. The documents in the package,
including this one, describe other possible uses.

History
=======

This is a refactoring of the ZODB-only parts of the zc.relationship package.
Specifically, the zc.relation catalog is largely equivalent to the
zc.relationship index. The index in the zc.relationship 2.x line is an
almost-completely backwards-compatible wrapper of the zc.relation catalog.
zc.relationship will continue to be maintained, though active development is
expected to go into zc.relation.

Many of the ideas come from discussions with and code from Casey Duncan, Tres
Seaver, Ken Manheimer, and more.

Setting Up a Relation Catalog
=============================

In this section, we will be introducing the following ideas.

- Relations are objects with indexed values.

- You add value indexes to relation catalogs to be able to search.  Values
  can be identified to the catalog with callables or interface elements. The
  indexed value must be specified to the catalog as a single value or a
  collection.

- Relations and their values are stored in the catalog as tokens: unique
  identifiers that you can resolve back to the original value. Integers are the
  most efficient tokens, but others can work fine too.

- Token type determines the BTree module needed.

- You must define your own functions for tokenizing and resolving tokens. These
  functions are registered with the catalog for the relations and for each of
  their value indexes.

- Relations are indexed with ``index``.

We will use a simple two way relation as our example here. A brief introduction
to a more complex RDF-style subject-predicate-object set up can be found later
in the document.

Creating the Catalog
--------------------

Imagine a two way relation from one value to another.  Let's say that we
are modeling a relation of people to their supervisors: an employee may
have a single supervisor.  For this first example, the relation between
employee and supervisor will be intrinsic: the employee has a pointer to
the supervisor, and the employee object itself represents the relation.

Let's say further, for simplicity, that employee names are unique and
can be used to represent employees.  We can use names as our "tokens".

Tokens are similar to the primary key in a relational database. A token is a
way to identify an object. It must sort reliably and you must be able to write
a callable that reliably resolves to the object given the right context. In
Zope 3, intids (zope.app.intid) and keyreferences (zope.app.keyreference) are
good examples of reasonable tokens.

As we'll see below, you provide a way to convert objects to tokens, and resolve
tokens to objects, for the relations, and for each value index individually.
They can be the all the same functions or completely different, depending on
your needs.

For speed, integers make the best tokens; followed by other
immutables like strings; followed by non-persistent objects; followed by
persistent objects.  The choice also determines a choice of BTree module, as
we'll see below.

Here is our toy ``Employee`` example class.  Again, we will use the employee
name as the tokens.

    >>> employees = {} # we'll use this to resolve the "name" tokens
    >>> class Employee(object):
    ...     def __init__(self, name, supervisor=None):
    ...         if name in employees:
    ...             raise ValueError('employee with same name already exists')
    ...         self.name = name # expect this to be readonly
    ...         self.supervisor = supervisor
    ...         employees[name] = self
    ...     # the next parts just make the tests prettier
    ...     def __repr__(self):
    ...         return '<Employee instance "' + self.name + '">'
    ...     def __cmp__(self, other):
    ...         # pukes if other doesn't have name
    ...         return cmp(self.name, other.name)
    ...

So, we need to define how to turn employees into their tokens.  We call the
tokenization a "dump" function. Conversely, the function to resolve tokens into
objects is called a "load".

Functions to dump relations and values get several arguments. The first
argument is the object to be tokenized. Next, because it helps sometimes to
provide context, is the catalog. The last argument is a dictionary that will be
shared for a given search. The dictionary can be ignored, or used as a cache
for optimizations (for instance, to stash a utility that you looked up).

For this example, our function is trivial: we said the token would be
the employee's name.

    >>> def dumpEmployees(emp, catalog, cache):
    ...     return emp.name
    ...

If you store the relation catalog persistently (e.g., in the ZODB) be aware
that the callables you provide must be picklable--a module-level function,
for instance.

We also need a way to turn tokens into employees, or "load".

The "load" functions get the token to be resolved; the catalog, for
context; and a dict cache, for optimizations of subsequent calls.

You might have noticed in our ``Employee.__init__`` that we keep a mapping
of name to object in the ``employees`` global dict (defined right above
the class definition).  We'll use that for resolving the tokens.  

    >>> def loadEmployees(token, catalog, cache):
    ...     return employees[token]
    ...

Now we know enough to get started with a catalog.  We'll instantiate it
by specifying how to tokenize relations, and what kind of BTree modules
should be used to hold the tokens.

How do you pick BTree modules?

- If the tokens are 32-bit ints, choose ``BTrees.family32.II``,
  ``BTrees.family32.IF`` or ``BTrees.family32.IO``.

- If the tokens are 64 bit ints, choose ``BTrees.family64.II``,
  ``BTrees.family64.IF`` or ``BTrees.family64.IO``.

- If they are anything else, choose ``BTrees.family32.OI``,
  ``BTrees.family64.OI``, or ``BTrees.family32.OO`` (or
  ``BTrees.family64.OO``--they are the same).

Within these rules, the choice is somewhat arbitrary unless you plan to merge
these results with that of another source that is using a particular BTree
module. BTree set operations only work within the same module, so you must
match module to module. The catalog defaults to IF trees, because that's what
standard zope catalogs use. That's as reasonable a choice as any, and will
potentially come in handy if your tokens are in fact the same as those used by
the zope catalog and you want to do some set operations.

In this example, our tokens are strings, so we want OO or an OI variant.  We'll
choose BTrees.family32.OI, arbitrarily.

    >>> import zc.relation.catalog
    >>> import BTrees
    >>> catalog = zc.relation.catalog.Catalog(dumpEmployees, loadEmployees,
    ...                                       btree=BTrees.family32.OI)

[#verifyObjectICatalog]_ [#legacy]_ Look! A relation catalog! We can't do very
much searching with it so far though, because the catalog doesn't have any
indexes.

In this example, the relation itself represents the employee, so we won't need
to index that separately.

But we do need a way to tell the catalog how to find the other end of the
relation, the supervisor. You can specify this to the catalog with an attribute
or method specified from ``zope.interface Interface``, or with a callable.
We'll use a callable for now. The callable will receive the indexed relation
and the catalog for context.

    >>> def supervisor(emp, catalog):
    ...     return emp.supervisor # None or another employee
    ...

We'll also need to specify how to tokenize (dump and load) those values. In
this case, we're able to use the same functions as the relations themselves.
However, do note that we can specify a completely different way to dump and
load for each "value index," or relation element.

We could also specify the name to call the index, but it will default to the
``__name__`` of the function (or interface element), which will work just fine
for us now.

Now we can add the "supervisor" value index.

    >>> catalog.addValueIndex(supervisor, dumpEmployees, loadEmployees,
    ...                       btree=BTrees.family32.OI)

Now we have an index [#addValueIndexExceptions]_.

    >>> [info['name'] for info in catalog.iterValueIndexInfo()]
    ['supervisor']

Adding Relations
----------------

Now let's create a few employees.  All but one will have supervisors. 
If you recall our toy ``Employee`` class, the first argument to the
constructor is the employee name (and therefore the token), and the
optional second argument is the supervisor.

    >>> a = Employee('Alice')
    >>> b = Employee('Betty', a)
    >>> c = Employee('Chuck', a)
    >>> d = Employee('Diane', b)
    >>> e = Employee('Edgar', b)
    >>> f = Employee('Frank', c)
    >>> g = Employee('Galyn', c)
    >>> h = Employee('Howie', d)

Here is a diagram of the hierarchy.

::

                Alice
             __/     \__
        Betty           Chuck
        /   \           /   \
    Diane   Edgar   Frank   Galyn
      |
    Howie

Let's tell the catalog about the relations, using the ``index`` method.

    >>> for emp in (a,b,c,d,e,f,g,h):
    ...     catalog.index(emp)
    ...

We've now created the relation catalog and added relations to it. We're ready
to search!

Searching
=========

In this section, we will introduce the following ideas.

- Queries to the relation catalog are formed with dicts.

- Query keys are the names of the indexes you want to search, or, for the
  special case of precise relations, the ``zc.relation.RELATION`` constant.

- Query values are the tokens of the results you want to match; or ``None``,
  indicating relations that have ``None`` as a value (or an empty collection,
  if it is a multiple). Search values can use
  ``zc.relation.catalog.any(args)`` or ``zc.relation.catalog.Any(args)`` to
  specify multiple (non-``None``) results to match for a given key.

- The index has a variety of methods to help you work with tokens.
  ``tokenizeQuery`` is typically the most used, though others are available.

- To find relations that match a query, use ``findRelations`` or
  ``findRelationTokens``.

- To find values that match a query, use ``findValues`` or ``findValueTokens``.

- You search transitively by using a query factory. The
  ``zc.relation.queryfactory.TransposingTransitive`` is a good common case
  factory that lets you walk up and down a hierarchy. A query factory can be
  passed in as an argument to search methods as a ``queryFactory``, or
  installed as a default behavior using ``addDefaultQueryFactory``.

- To find how a query is related, use ``findRelationChains`` or
  ``findRelationTokenChains``.

- To find out if a query is related, use ``canFind``.

- Circular transitive relations are handled to prevent infinite loops. They
  are identified in ``findRelationChains`` and ``findRelationTokenChains`` with
  a ``zc.relation.interfaces.ICircularRelationPath`` marker interface.

- search methods share the following arguments:

  * ``maxDepth``, limiting the transitive depth for searches;
  
  * ``filter``, allowing code to filter transitive paths;
  
  * ``targetQuery``, allowing a query to filter transitive paths on the basis
    of the endpoint;
  
  * ``targetFilter``, allowing code to filter transitive paths on the basis of
    the endpoint; and

  * ``queryFactory``, mentioned above.

- You can set up search indexes to speed up specific transitive searches.

Queries, ``findRelations``, and special query values
----------------------------------------------------

So who works for Alice?  That means we want to get the relations--the
employees--with a ``supervisor`` of Alice.

The heart of a question to the catalog is a query.  A query is spelled
as a dictionary.  The main idea is simply that keys in a dictionary
specify index names, and the values specify the constraints.

The values in a query are always expressed with tokens.  The catalog has
several helpers to make this less onerous, but for now let's take
advantage of the fact that our tokens are easily comprehensible.

    >>> sorted(catalog.findRelations({'supervisor': 'Alice'}))
    [<Employee instance "Betty">, <Employee instance "Chuck">]

Alice is the direct (intransitive) boss of Betty and Chuck.

What if you want to ask "who doesn't report to anyone?"  Then you want to
ask for a relation in which the supervisor is None.

    >>> list(catalog.findRelations({'supervisor': None}))
    [<Employee instance "Alice">]

Alice is the only employee who doesn't report to anyone.

What if you want to ask "who reports to Diane or Chuck?"  Then you use the
zc.relation ``Any`` class or ``any`` function to pass the multiple values.

    >>> sorted(catalog.findRelations(
    ...     {'supervisor': zc.relation.catalog.any('Diane', 'Chuck')}))
    ... # doctest: +NORMALIZE_WHITESPACE
    [<Employee instance "Frank">, <Employee instance "Galyn">,
     <Employee instance "Howie">]

Frank, Galyn, and Howie each report to either Diane or Chuck. [#any]_

``findValues`` and the ``RELATION`` query key
---------------------------------------------

So how do we find who an employee's supervisor is?  Well, in this case,
look at the attribute on the employee!  If you can use an attribute that
will usually be a win in the ZODB.  

    >>> h.supervisor
    <Employee instance "Diane">

Again, as we mentioned at the start of this first example, the knowledge
of a supervisor is "intrinsic" to the employee instance.  It is
possible, and even easy, to ask the catalog this kind of question, but
the catalog syntax is more geared to "extrinsic" relations, such as the
one from the supervisor to the employee: the connection between a
supervisor object and its employees is extrinsic to the supervisor, so
you actually might want a catalog to find it!

However, we will explore the syntax very briefly, because it introduces an
important pair of search methods, and because it is a stepping stone
to our first transitive search.

So, o relation catalog, who is Howie's supervisor?  

To ask this question we want to get the indexed values off of the relations:
``findValues``. In its simplest form, the arguments are the index name of the
values you want, and a query to find the relations that have the desired
values.

What about the query? Above, we noted that the keys in a query are the names of
the indexes to search. However, in this case, we don't want to search one or
more indexes for matching relations, as usual, but actually specify a relation:
Howie.

We do not have a value index name: we are looking for a relation. The query
key, then, should be the constant ``zc.relation.RELATION``. For our current
example, that would mean the query is ``{zc.relation.RELATION: 'Howie'}``.

    >>> import zc.relation
    >>> list(catalog.findValues(
    ...     'supervisor', {zc.relation.RELATION: 'Howie'}))[0]
    <Employee instance "Diane">

Congratulations, you just found an obfuscated and comparitively
inefficient way to write ``howie.supervisor``! [#intrinsic_search]_
[#findValuesExceptions]_

Slightly more usefully, you can use other query keys along with
zc.relation.RELATION. This asks, "Of Betty, Alice, and Frank, who are
supervised by Alice?"
    
    >>> sorted(catalog.findRelations(
    ...     {zc.relation.RELATION: zc.relation.catalog.any(
    ...         'Betty', 'Alice', 'Frank'),
    ...      'supervisor': 'Alice'}))
    [<Employee instance "Betty">]

Only Betty is.

Tokens
------

As mentioned above, the catalog provides several helpers to work with tokens.
The most frequently used is ``tokenizeQuery``, which takes a query with object
values and converts them to tokens using the "dump" functions registered for
the relations and indexed values. Here are alternate spellings of some of the
queries we've encountered above.

    >>> catalog.tokenizeQuery({'supervisor': a})
    {'supervisor': 'Alice'}
    >>> catalog.tokenizeQuery({'supervisor': None})
    {'supervisor': None}
    >>> import pprint
    >>> catalog.tokenizeQuery(
    ...     {zc.relation.RELATION: zc.relation.catalog.any(a, b, f),
    ...     'supervisor': a}) # doctest: +NORMALIZE_WHITESPACE
    {None: <zc.relation.catalog.Any instance ('Alice', 'Betty', 'Frank')>,
    'supervisor': 'Alice'}

(If you are wondering about that ``None`` in the last result, yes,
``zc.relation.RELATION`` is just readability sugar for ``None``.)

So, here's a real search using ``tokenizeQuery``.  We'll make an alias for
``catalog.tokenizeQuery`` just to shorten things up a bit.

    >>> query = catalog.tokenizeQuery
    >>> sorted(catalog.findRelations(query(
    ...     {zc.relation.RELATION: zc.relation.catalog.any(a, b, f),
    ...      'supervisor': a})))
    [<Employee instance "Betty">]

The catalog always has parallel search methods, one for finding objects, as
seen above, and one for finding tokens (the only exception is ``canFind``,
described below). Finding tokens can be much more efficient, especially if the
result from the relation catalog is just one step along the path of finding
your desired result. But finding objects is simpler for some common cases.
Here's a quick example of some queries above, getting tokens rather than
objects.

You can also spell a query in ``tokenizeQuery`` with keyword arguments. This
won't work if your key is ``zc.relation.RELATION``, but otherwise it can
improve readability. We'll see some examples of this below as well.

    >>> sorted(catalog.findRelationTokens(query(supervisor=a)))
    ['Betty', 'Chuck']

    >>> sorted(catalog.findRelationTokens({'supervisor': None}))
    ['Alice']

    >>> sorted(catalog.findRelationTokens(
    ...     query(supervisor=zc.relation.catalog.any(c, d))))
    ['Frank', 'Galyn', 'Howie']

    >>> sorted(catalog.findRelationTokens(
    ...     query({zc.relation.RELATION: zc.relation.catalog.any(a, b, f),
    ...            'supervisor': a})))
    ['Betty']

The catalog provides several other methods just for working with tokens.

- ``resolveQuery``: the inverse of ``tokenizeQuery``, converting a
  tokenizedquery to a query with objects.

- ``tokenizeValues``: returns an iterable of tokens for the values of the given
  index name.

- ``resolveValueTokens``: returns an iterable of values for the tokens of the
  given index name.

- ``tokenizeRelation``: returns a token for the given relation.

- ``resolveRelationToken``: returns a relation for the given token.

- ``tokenizeRelations``: returns an iterable of tokens for the relations given.

- ``resolveRelationTokens``: returns an iterable of relations for the tokens
  given.

These methods are lesser used, and described in more technical documents in
this package.

Transitive Searching, Query Factories, and ``maxDepth``
-------------------------------------------------------

So, we've seen a lot of one-level, intransitive searching. What about
transitive searching? Well, you need to tell the catalog how to walk the tree.
In simple (and very common) cases like this, the
``zc.relation.queryfactory.TransposingTransitive`` will do the trick.

A transitive query factory is just a callable that the catalog uses to
ask "I got this query, and here are the results I found. I'm supposed to
walk another step transitively, so what query should I search for next?"
Writing a factory is more complex than we want to talk about right now,
but using the ``TransposingTransitiveQueryFactory`` is easy. You just tell
it the two query names it should transpose for walking in either
direction.

For instance, here we just want to tell the factory to transpose the two keys
we've used, ``zc.relation.RELATION`` and 'supervisor'. Let's make a factory,
use it in a query for a couple of transitive searches, and then, if you want,
you can read through a footnote to talk through what is happening.

Here's the factory.

    >>> import zc.relation.queryfactory
    >>> factory = zc.relation.queryfactory.TransposingTransitive(
    ...     zc.relation.RELATION, 'supervisor')

Now ``factory`` is just a callable.  Let's let it help answer a couple of
questions.

Who are all of Howie's supervisors transitively (this looks up in the
diagram)?

    >>> list(catalog.findValues('supervisor', {zc.relation.RELATION: 'Howie'},
    ...      queryFactory=factory))
    ... # doctest: +NORMALIZE_WHITESPACE
    [<Employee instance "Diane">, <Employee instance "Betty">,
     <Employee instance "Alice">]

Who are all of the people Betty supervises transitively, breadth first (this
looks down in the diagram)?

    >>> people = list(catalog.findRelations(
    ...     {'supervisor': 'Betty'}, queryFactory=factory))
    >>> sorted(people[:2])
    [<Employee instance "Diane">, <Employee instance "Edgar">]
    >>> people[2]
    <Employee instance "Howie">

Yup, that looks right.  So how did that work?  If you care, read this
footnote. [#I_care]_
    
This transitive factory is really the only transitive factory you would
want for this particular catalog, so it probably is safe to wire it in
as a default.  You can add multiple query factories to match different
queries using ``addDefaultQueryFactory``.

    >>> catalog.addDefaultQueryFactory(factory)

Now all searches are transitive by default.

    >>> list(catalog.findValues('supervisor', {zc.relation.RELATION: 'Howie'}))
    ... # doctest: +NORMALIZE_WHITESPACE
    [<Employee instance "Diane">, <Employee instance "Betty">,
     <Employee instance "Alice">]
    >>> people = list(catalog.findRelations({'supervisor': 'Betty'}))
    >>> sorted(people[:2])
    [<Employee instance "Diane">, <Employee instance "Edgar">]
    >>> people[2]
    <Employee instance "Howie">

We can force a non-transitive search, or a specific search depth, with
``maxDepth`` [#needs_a_transitive_queries_factory]_.

    >>> list(catalog.findValues(
    ...     'supervisor', {zc.relation.RELATION: 'Howie'}, maxDepth=1))
    [<Employee instance "Diane">]
    >>> sorted(catalog.findRelations({'supervisor': 'Betty'}, maxDepth=1))
    [<Employee instance "Diane">, <Employee instance "Edgar">]

[#maxDepthExceptions]_ We'll introduce some other available search
arguments later in this document and in other documents.  It's important
to note that *all search methods share the same arguments as
``findRelations``*.  ``findValues`` and ``findValueTokens`` only add the
initial argument of specifying the desired value.

We've looked at two search methods so far: the ``findValues`` and
``findRelations`` methods help you ask what is related.  But what if you
want to know *how* things are transitively related?

``findRelationChains`` and ``targetQuery``
------------------------------------------

Another search method, ``findRelationChains``, helps you discover how
things are transitively related.  

The method name says "find relation chains".  But what is a "relation
chain"?  In this API, it is a transitive path of relations.  For
instance, what's the chain of command above Howie?  ``findRelationChains``
will return each unique path.

    >>> list(catalog.findRelationChains({zc.relation.RELATION: 'Howie'}))
    ... # doctest: +NORMALIZE_WHITESPACE
    [(<Employee instance "Howie">,),
     (<Employee instance "Howie">, <Employee instance "Diane">),
     (<Employee instance "Howie">, <Employee instance "Diane">,
      <Employee instance "Betty">),
     (<Employee instance "Howie">, <Employee instance "Diane">,
     <Employee instance "Betty">, <Employee instance "Alice">)]

Look at that result carefully.  Notice that the result is an iterable of
tuples.  Each tuple is a unique chain, which may be a part of a
subsequent chain.  In this case, the last chain is the longest and the
most comprehensive.

What if we wanted to see all the paths from Alice?  That will be one
chain for each supervised employee, because it shows all possible paths.

    >>> sorted(catalog.findRelationChains(
    ...     {'supervisor': 'Alice'}))
    ... # doctest: +NORMALIZE_WHITESPACE
    [(<Employee instance "Betty">,),
     (<Employee instance "Betty">, <Employee instance "Diane">),
     (<Employee instance "Betty">, <Employee instance "Diane">,
      <Employee instance "Howie">),
     (<Employee instance "Betty">, <Employee instance "Edgar">),
     (<Employee instance "Chuck">,),
     (<Employee instance "Chuck">, <Employee instance "Frank">),
     (<Employee instance "Chuck">, <Employee instance "Galyn">)]

That's all the paths--all the chains--from Alice.  We sorted the results,
but normally they would be breadth first.

But what if we wanted to just find the paths from one query result to
another query result--say, we wanted to know the chain of command from Alice
down to Howie?  Then we can specify a ``targetQuery`` that specifies the
characteristics of our desired end point (or points).

    >>> list(catalog.findRelationChains(
    ...     {'supervisor': 'Alice'},
    ...     targetQuery={zc.relation.RELATION: 'Howie'}))
    ... # doctest: +NORMALIZE_WHITESPACE
    [(<Employee instance "Betty">, <Employee instance "Diane">,
      <Employee instance "Howie">)]

So, Betty supervises Diane, who supervises Howie.

Note that ``targetQuery`` now joins ``maxDepth`` in our collection of shared
search arguments that we have introduced.

``filter`` and ``targetFilter``
-------------------------------

We can take a quick look now at the last of the two shared search arguments:
``filter`` and ``targetFilter``.  These two are similar in that they both are
callables that can approve or reject given relations in a search based on
whatever logic you can code.  They differ in that ``filter`` stops any further
transitive searches from the relation, while ``targetFilter`` merely omits the
given result but allows further search from it.  Like ``targetQuery``, then,
``targetFilter`` is good when you want to specify the other end of a path.

As an example, let's say we only want to return female employees.

    >>> female_employees = ('Alice', 'Betty', 'Diane', 'Galyn')
    >>> def female_filter(relchain, query, catalog, cache):
    ...     return relchain[-1] in female_employees
    ...

Here are all the female employees supervised by Alice transitively, using
``targetFilter``.

    >>> list(catalog.findRelations({'supervisor': 'Alice'},
    ...                            targetFilter=female_filter))
    ... # doctest: +NORMALIZE_WHITESPACE
    [<Employee instance "Betty">, <Employee instance "Diane">,
     <Employee instance "Galyn">]

Here are all the female employees supervised by Chuck.

    >>> list(catalog.findRelations({'supervisor': 'Chuck'},
    ...                            targetFilter=female_filter))
    [<Employee instance "Galyn">]

The same method used as a filter will only return females directly
supervised by other females--not Galyn, in this case.

    >>> list(catalog.findRelations({'supervisor': 'Alice'},
    ...                            filter=female_filter))
    [<Employee instance "Betty">, <Employee instance "Diane">]

These can be combined with one another, and with the other search
arguments [#filter]_.

Search indexes
--------------

Without setting up any additional indexes, the transitive behavior of
the ``findRelations`` and ``findValues`` methods essentially relies on the
brute force searches of ``findRelationChains``.  Results are iterables
that are gradually computed.  For instance, let's repeat the question
"Whom does Betty supervise?".  Notice that ``res`` first populates a list
with three members, but then does not populate a second list.  The
iterator has been exhausted.

    >>> res = catalog.findRelationTokens({'supervisor': 'Betty'})
    >>> unindexed = sorted(res)
    >>> len(unindexed)
    3
    >>> len(list(res)) # iterator is exhausted
    0

The brute force of this approach can be sufficient in many cases, but
sometimes speed for these searches is critical.  In these cases, you can
add a "search index".  A search index speeds up the result of one or
more precise searches by indexing the results.  Search indexes can
affect the results of searches with a ``queryFactory`` in ``findRelations``,
``findValues``, and the soon-to-be-introduced ``canFind``, but they do not
affect ``findRelationChains``.

The zc.relation package currently includes two kinds of search indexes, one for
indexing transitive membership searches in a hierarchy and one for intransitive
searches explored in tokens.txt in this package, which can optimize frequent
searches on complex queries or can effectively change the meaning of an
intransitive search. Other search index implementations and approaches may be
added in the future. 

Here's a very brief example of adding a search index for the transitive
searches seen above that specify a 'supervisor'.

    >>> import zc.relation.searchindex
    >>> catalog.addSearchIndex(
    ...     zc.relation.searchindex.TransposingTransitiveMembership(
    ...         'supervisor', zc.relation.RELATION))

The ``zc.relation.RELATION`` describes how to walk back up the chain. Search
indexes are explained in reasonable detail in searchindex.txt.

Now that we have added the index, we can search again.  The result this
time is already computed, so, at least when you ask for tokens, it
is repeatable.

    >>> res = catalog.findRelationTokens({'supervisor': 'Betty'})
    >>> len(list(res))
    3
    >>> len(list(res))
    3
    >>> sorted(res) == unindexed
    True

Note that the breadth-first sorting is lost when an index is used [#updates]_.

Transitive cycles (and updating and removing relations)
-------------------------------------------------------

The transitive searches and the provided search indexes can handle
cycles.  Cycles are less likely in the current example than some others,
but we can stretch the case a bit: imagine a "king in disguise", in
which someone at the top works lower in the hierarchy.  Perhaps Alice
works for Zane, who works for Betty, who works for Alice.  Artificial,
but easy enough to draw::

            ______
           /      \
          /     Zane
         /        |
        /       Alice
       /     __/     \__
      / Betty__         Chuck
      \-/  /   \         /   \
         Diane Edgar Frank   Galyn
          |
        Howie

Easy to create too.

    >>> z = Employee('Zane', b)
    >>> a.supervisor = z

Now we have a cycle.  Of course, we have not yet told the catalog about it.
``index`` can be used both to reindex Alice and index Zane.

    >>> catalog.index(a)
    >>> catalog.index(z)

Now, if we ask who works for Betty, we get the entire tree.  (We'll ask
for tokens, just so that the result is smaller to look at.) [#same_set]_

    >>> sorted(catalog.findRelationTokens({'supervisor': 'Betty'}))
    ... # doctest: +NORMALIZE_WHITESPACE
    ['Alice', 'Betty', 'Chuck', 'Diane', 'Edgar', 'Frank', 'Galyn', 'Howie',
     'Zane']

If we ask for the supervisors of Frank, it will include Betty.

    >>> list(catalog.findValueTokens(
    ...     'supervisor', {zc.relation.RELATION: 'Frank'}))
    ['Chuck', 'Alice', 'Zane', 'Betty']

Paths returned by ``findRelationChains`` are marked with special interfaces,
and special metadata, to show the chain.

    >>> res = list(catalog.findRelationChains({zc.relation.RELATION: 'Frank'}))
    >>> len(res)
    5
    >>> import zc.relation.interfaces
    >>> [zc.relation.interfaces.ICircularRelationPath.providedBy(r)
    ...  for r in res]
    [False, False, False, False, True]

Here's the last chain:
    
    >>> res[-1] # doctest: +NORMALIZE_WHITESPACE
    cycle(<Employee instance "Frank">, <Employee instance "Chuck">,
          <Employee instance "Alice">, <Employee instance "Zane">,
          <Employee instance "Betty">)

The chain's 'cycled' attribute has a list of queries that create a cycle.
If you run the query, or queries, you see where the cycle would
restart--where the path would have started to overlap.  Sometimes the query
results will include multiple cycles, and some paths that are not cycles.
In this case, there's only a single cycled query, which results in a single
cycled relation.

    >>> len(res[4].cycled)
    1

    >>> list(catalog.findRelations(res[4].cycled[0], maxDepth=1))
    [<Employee instance "Alice">]

To remove this craziness [#reverse_lookup]_, we can unindex Zane, and change
and reindex Alice.

    >>> a.supervisor = None
    >>> catalog.index(a)

    >>> list(catalog.findValueTokens(
    ...     'supervisor', {zc.relation.RELATION: 'Frank'}))
    ['Chuck', 'Alice']

    >>> catalog.unindex(z)

    >>> sorted(catalog.findRelationTokens({'supervisor': 'Betty'}))
    ['Diane', 'Edgar', 'Howie']

``canFind``
-----------

We're to the last search method: ``canFind``.  We've gotten values and
relations, but what if you simply want to know if there is any
connection at all?  For instance, is Alice a supervisor of Howie? Is
Chuck?  To answer these questions, you can use the ``canFind`` method
combined with the ``targetQuery`` search argument.

The ``canFind`` method takes the same arguments as findRelations.  However,
it simply returns a boolean about whether the search has any results.  This
is a convenience that also allows some extra optimizations.

Does Betty supervise anyone?

    >>> catalog.canFind({'supervisor': 'Betty'})
    True

What about Howie?

    >>> catalog.canFind({'supervisor': 'Howie'})
    False

What about...Zane (no longer an employee)?

    >>> catalog.canFind({'supervisor': 'Zane'})
    False

If we want to know if Alice or Chuck supervise Howie, then we want to specify
characteristics of two points on a path.  To ask a question about the other
end of a path, use ``targetQuery``.

Is Alice a supervisor of Howie?

    >>> catalog.canFind({'supervisor': 'Alice'},
    ...                 targetQuery={zc.relation.RELATION: 'Howie'})
    True

Is Chuck a supervisor of Howie?

    >>> catalog.canFind({'supervisor': 'Chuck'},
    ...                 targetQuery={zc.relation.RELATION: 'Howie'})
    False

Is Howie Alice's employee?

    >>> catalog.canFind({zc.relation.RELATION: 'Howie'},
    ...                 targetQuery={'supervisor': 'Alice'})
    True

Is Howie Chuck's employee?

    >>> catalog.canFind({zc.relation.RELATION: 'Howie'},
    ...                 targetQuery={'supervisor': 'Chuck'})
    False

(Note that, if your relations describe a hierarchy, searching up a hierarchy is
usually more efficient than searching down, so the second pair of questions is
generally preferable to the first in that case.)

Working with More Complex Relations
===================================

So far, our examples have used a simple relation, in which the indexed object
is one end of the relation, and the indexed value on the object is the other.
This example has let us look at all of the basic zc.relation catalog
functionality.

As mentioned in the introduction, though, the catalog supports, and was
designed for, more complex relations.  This section will quickly examine a
few examples of other uses.

In this section, we will see several examples of ideas mentioned above but not
yet demonstrated.

- We can use interface attributes (values or callables) to define value
  indexes.

- Using interface attributes will cause an attempt to adapt the relation if it
  does not already provide the interface.

- We can use the ``multiple`` argument when defining a value index to indicate
  that the indexed value is a collection.

- We can use the ``name`` argument when defining a value index to specify the
  name to be used in queries, rather than relying on the name of the interface
  attribute or callable.

- The ``family`` argument in instantiating the catalog lets you change the
  default btree family for relations and value indexes from
  ``BTrees.family32.IF`` to ``BTrees.family64.IF``.

Extrinsic Two-Way Relations
---------------------------

A simple variation of our current story is this: what if the indexed relation
were between two other objects--that is, what if the relation were extrinsic to
both participants?

Let's imagine we have relations that show biological parentage. We'll want a
"Person" and a "Parentage" relation. We'll define an interface for
``IParentage`` so we can see how using an interface to define a value index
works.

    >>> class Person(object):
    ...     def __init__(self, name):
    ...         self.name = name
    ...     def __repr__(self):
    ...         return '<Person %r>' % (self.name,)
    ...
    >>> import zope.interface
    >>> class IParentage(zope.interface.Interface):
    ...     child = zope.interface.Attribute('the child')
    ...     parents = zope.interface.Attribute('the parents')
    ...
    >>> class Parentage(object):
    ...     zope.interface.implements(IParentage)
    ...     def __init__(self, child, parent1, parent2):
    ...         self.child = child
    ...         self.parents = (parent1, parent2)
    ...

Now we'll define the dumpers and loaders and then the catalog.  Notice that
we are relying on a pattern: the dump must be called before the load.

    >>> _people = {}
    >>> _relations = {}
    >>> def dumpPeople(obj, catalog, cache):
    ...     if _people.setdefault(obj.name, obj) is not obj:
    ...         raise ValueError('we are assuming names are unique')
    ...     return obj.name
    ...
    >>> def loadPeople(token, catalog, cache):
    ...     return _people[token]
    ...
    >>> def dumpRelations(obj, catalog, cache):
    ...     if _relations.setdefault(id(obj), obj) is not obj:
    ...         raise ValueError('huh?')
    ...     return id(obj)
    ...
    >>> def loadRelations(token, catalog, cache):
    ...     return _relations[token]
    ...
    >>> catalog = zc.relation.catalog.Catalog(dumpRelations, loadRelations)
    >>> catalog.addValueIndex(IParentage['child'], dumpPeople, loadPeople,
    ...                       btree=BTrees.family32.OO)
    >>> catalog.addValueIndex(IParentage['parents'], dumpPeople, loadPeople,
    ...                       btree=BTrees.family32.OO, multiple=True,
    ...                       name='parent')
    >>> catalog.addDefaultQueryFactory(
    ...     zc.relation.queryfactory.TransposingTransitive(
    ...         'child', 'parent'))

Now we have a catalog fully set up.  Let's add some relations.

    >>> a = Person('Alice')
    >>> b = Person('Betty')
    >>> c = Person('Charles')
    >>> d = Person('Donald')
    >>> e = Person('Eugenia')
    >>> f = Person('Fred')
    >>> g = Person('Gertrude')
    >>> h = Person('Harry')
    >>> i = Person('Iphigenia')
    >>> j = Person('Jacob')
    >>> k = Person('Karyn')
    >>> l = Person('Lee')

    >>> r1 = Parentage(child=j, parent1=k, parent2=l)
    >>> r2 = Parentage(child=g, parent1=i, parent2=j)
    >>> r3 = Parentage(child=f, parent1=g, parent2=h)
    >>> r4 = Parentage(child=e, parent1=g, parent2=h)
    >>> r5 = Parentage(child=b, parent1=e, parent2=d)
    >>> r6 = Parentage(child=a, parent1=e, parent2=c)

Here's that in one of our hierarchy diagrams.

::

    Karyn   Lee
         \ /
        Jacob   Iphigenia
             \ /
            Gertrude    Harry
                    \  /
                 /-------\
             Fred        Eugenia
               Donald   /     \    Charles
                     \ /       \  /
                    Betty      Alice

Now we can index the relations, and ask some questions.

    >>> for r in (r1, r2, r3, r4, r5, r6):
    ...     catalog.index(r)
    >>> query = catalog.tokenizeQuery
    >>> sorted(catalog.findValueTokens(
    ...     'parent', query(child=a), maxDepth=1))
    ['Charles', 'Eugenia']
    >>> sorted(catalog.findValueTokens('parent', query(child=g)))
    ['Iphigenia', 'Jacob', 'Karyn', 'Lee']
    >>> sorted(catalog.findValueTokens(
    ...     'child', query(parent=h), maxDepth=1))
    ['Eugenia', 'Fred']
    >>> sorted(catalog.findValueTokens('child', query(parent=h)))
    ['Alice', 'Betty', 'Eugenia', 'Fred']
    >>> catalog.canFind(query(parent=h), targetQuery=query(child=d))
    False
    >>> catalog.canFind(query(parent=l), targetQuery=query(child=b))
    True

Multi-Way Relations
-------------------

The previous example quickly showed how to set the catalog up for a completely
extrinsic two-way relation.  The same pattern can be extended for N-way
relations.  For example, consider a four way relation in the form of
SUBJECTS PREDICATE OBJECTS [in CONTEXT].  For instance, we might
want to say "(joe,) SELLS (doughnuts, coffee) in corner_store", where "(joe,)"
is the collection of subjects, "SELLS" is the predicate, "(doughnuts, coffee)"
is the collection of objects, and "corner_store" is the optional context.

For this last example, we'll integrate two components we haven't seen examples
of here before: the ZODB and adaptation.

Our example ZODB approach uses OIDs as the tokens. this might be OK in some
cases, if you will never support multiple databases and you don't need an
abstraction layer so that a different object can have the same identifier.

    >>> import persistent
    >>> import struct
    >>> class Demo(persistent.Persistent):
    ...     def __init__(self, name):
    ...         self.name = name
    ...     def __repr__(self):
    ...         return '<Demo instance %r>' % (self.name,)
    ...
    >>> class IRelation(zope.interface.Interface):
    ...     subjects = zope.interface.Attribute('subjects')
    ...     predicate = zope.interface.Attribute('predicate')
    ...     objects = zope.interface.Attribute('objects')
    ...
    >>> class IContextual(zope.interface.Interface):
    ...     def getContext():
    ...         'return context'
    ...     def setContext(value):
    ...         'set context'
    ...
    >>> class Contextual(object):
    ...     zope.interface.implements(IContextual)
    ...     _context = None
    ...     def getContext(self):
    ...         return self._context
    ...     def setContext(self, value):
    ...         self._context = value
    ...
    >>> class Relation(persistent.Persistent):
    ...     zope.interface.implements(IRelation)
    ...     def __init__(self, subjects, predicate, objects):
    ...         self.subjects = subjects
    ...         self.predicate = predicate
    ...         self.objects = objects
    ...         self._contextual = Contextual()
    ...
    ...     def __conform__(self, iface):
    ...         if iface is IContextual:
    ...             return self._contextual
    ...

(When using zope.component, the ``__conform__`` would normally be unnecessary;
however, this package does not depend on zope.component.)

    >>> def dumpPersistent(obj, catalog, cache):
    ...     if obj._p_jar is None:
    ...         catalog._p_jar.add(obj) # assumes something else places it
    ...     return struct.unpack('<q', obj._p_oid)[0]
    ...
    >>> def loadPersistent(token, catalog, cache):
    ...     return catalog._p_jar.get(struct.pack('<q', token))
    ...

    >>> from ZODB.tests.util import DB
    >>> db = DB()
    >>> conn = db.open()
    >>> root = conn.root()
    >>> catalog = root['catalog'] = zc.relation.catalog.Catalog(
    ...     dumpPersistent, loadPersistent, family=BTrees.family64)
    >>> catalog.addValueIndex(IRelation['subjects'],
    ...     dumpPersistent, loadPersistent, multiple=True, name='subject')
    >>> catalog.addValueIndex(IRelation['objects'],
    ...     dumpPersistent, loadPersistent, multiple=True, name='object')
    >>> catalog.addValueIndex(IRelation['predicate'], btree=BTrees.family32.OO)
    >>> catalog.addValueIndex(IContextual['getContext'],
    ...     dumpPersistent, loadPersistent, name='context')
    >>> import transaction
    >>> transaction.commit()

The ``dumpPersistent`` and ``loadPersistent`` is a bit of a toy, as warned
above. Also, while our predicate will be stored as a string, some programmers
may prefer to have a dump in such a case verify that the string has been
explicitly registered in some way, to prevent typos. Obviously, we are not
bothering with this for our example.

We make some objects, and then we make some relations with those objects and
index them.

    >>> joe = root['joe'] = Demo('joe')
    >>> sara = root['sara'] = Demo('sara')
    >>> jack = root['jack'] = Demo('jack')
    >>> ann = root['ann'] = Demo('ann')
    >>> doughnuts = root['doughnuts'] = Demo('doughnuts')
    >>> coffee = root['coffee'] = Demo('coffee')
    >>> muffins = root['muffins'] = Demo('muffins')
    >>> cookies = root['cookies'] = Demo('cookies')
    >>> newspaper = root['newspaper'] = Demo('newspaper')
    >>> corner_store = root['corner_store'] = Demo('corner_store')
    >>> bistro = root['bistro'] = Demo('bistro')
    >>> bakery = root['bakery'] = Demo('bakery')

    >>> SELLS = 'SELLS'
    >>> BUYS = 'BUYS'
    >>> OBSERVES = 'OBSERVES'

    >>> rel1 = root['rel1'] = Relation((joe,), SELLS, (doughnuts, coffee))
    >>> IContextual(rel1).setContext(corner_store)
    >>> rel2 = root['rel2'] = Relation((sara, jack), SELLS,
    ...                                (muffins, doughnuts, cookies))
    >>> IContextual(rel2).setContext(bakery)
    >>> rel3 = root['rel3'] = Relation((ann,), BUYS, (doughnuts,))
    >>> rel4 = root['rel4'] = Relation((sara,), BUYS, (bistro,))
    
    >>> for r in (rel1, rel2, rel3, rel4):
    ...     catalog.index(r)
    ...

Now we can ask a simple question.  Where do they sell doughnuts?

    >>> query = catalog.tokenizeQuery
    >>> sorted(catalog.findValues(
    ...     'context',
    ...     (query(predicate=SELLS, object=doughnuts))),
    ...     key=lambda ob: ob.name)
    [<Demo instance 'bakery'>, <Demo instance 'corner_store'>]

Hopefully these examples give you further ideas on how you can use this tool.

Additional Functionality
========================

This section introduces peripheral functionality.  We will learn the following.

- Listeners can be registered in the catalog.  They are alerted when a relation
  is added, modified, or removed; and when the catalog is cleared and copied
  (see below).

- The ``clear`` method clears the relations in the catalog.

- The ``copy`` method makes a copy of the current catalog by copying internal
  data structures, rather than reindexing the relations, which can be a
  significant optimization opportunity.  This copies value indexes and search
  indexes; and gives listeners an opportunity to specify what, if anything,
  should be included in the new copy.

- The ``ignoreSearchIndex`` argument to the five pertinent search methods
  causes the search to ignore search indexes, even if there is an appropriate
  one.

- ``findRelationTokens()`` (without arguments) returns the BTree set of all
  relation tokens in the catalog.

- ``findValueTokens(INDEX_NAME)`` (where "INDEX_NAME" should be replaced with
  an index name) returns the BTree set of all value tokens in the catalog for
  the given index name.

Listeners
---------

A variety of potential clients may want to be alerted when the catalog changes.
zc.relation does not depend on zope.event, so listeners may be registered for
various changes.  Let's make a quick demo listener.  The ``additions`` and
``removals`` arguments are dictionaries of {value name: iterable of added or
removed value tokens}.

    >>> def pchange(d):
    ...     pprint.pprint(dict(
    ...         (k, v is not None and set(v) or v) for k, v in d.items()))
    >>> class DemoListener(persistent.Persistent):
    ...     zope.interface.implements(zc.relation.interfaces.IListener)
    ...     def relationAdded(self, token, catalog, additions):
    ...         print ('a relation (token %r) was added to %r '
    ...                'with these values:' % (token, catalog))
    ...         pchange(additions)
    ...     def relationModified(self, token, catalog, additions, removals):
    ...         print ('a relation (token %r) in %r was modified '
    ...                'with these additions:' % (token, catalog))
    ...         pchange(additions)
    ...         print 'and these removals:'
    ...         pchange(removals)
    ...     def relationRemoved(self, token, catalog, removals):
    ...         print ('a relation (token %r) was removed from %r '
    ...                'with these values:' % (token, catalog))
    ...         pchange(removals)
    ...     def sourceCleared(self, catalog):
    ...         print 'catalog %r had all relations unindexed' % (catalog,)
    ...     def sourceAdded(self, catalog):
    ...         print 'now listening to catalog %r' % (catalog,)
    ...     def sourceRemoved(self, catalog):
    ...         print 'no longer listening to catalog %r' % (catalog,)
    ...     def sourceCopied(self, original, copy):
    ...         print 'catalog %r made a copy %r' % (catalog, copy)
    ...         copy.addListener(self)
    ...

Listeners can be installed multiple times.

Listeners can be added as persistent weak references, so that, if they are
deleted elsewhere, a ZODB pack will not consider the reference in the catalog
to be something preventing garbage collection.

We'll install one of these demo listeners into our new catalog as a
normal reference, the default behavior.  Then we'll show some example messages
sent to the demo listener.

    >>> listener = DemoListener()
    >>> catalog.addListener(listener) # doctest: +ELLIPSIS
    now listening to catalog <zc.relation.catalog.Catalog object at ...>
    >>> rel5 = root['rel5'] = Relation((ann,), OBSERVES, (newspaper,))
    >>> catalog.index(rel5) # doctest: +ELLIPSIS
    a relation (token ...) was added to <...Catalog...> with these values:
    {'context': None,
     'object': set([...]),
     'predicate': set(['OBSERVES']),
     'subject': set([...])}
    >>> rel5.subjects = (jack,)
    >>> IContextual(rel5).setContext(bistro)
    >>> catalog.index(rel5) # doctest: +ELLIPSIS
    a relation (token ...) in ...Catalog... was modified with these additions:
    {'context': set([...]),
     'subject': set([...])}
    and these removals:
    {'subject': set([...])}
    >>> catalog.unindex(rel5) # doctest: +ELLIPSIS
    a relation (token ...) was removed from <...Catalog...> with these values:
    {'context': set([...]),
     'object': set([...]),
     'predicate': set(['OBSERVES']),
     'subject': set([...])}

    >>> catalog.removeListener(listener) # doctest: +ELLIPSIS
    no longer listening to catalog <...Catalog...>
    >>> catalog.index(rel5) # doctest: +ELLIPSIS

The only two methods not shown by those examples are ``sourceCleared`` and
``sourceCopied``.  We'll get to those very soon below.

The ``clear`` Method
--------------------

The ``clear`` method simply indexes all relations from a catalog.  Installed
listeners have ``sourceCleared`` called.

    >>> len(catalog)
    5

    >>> catalog.addListener(listener) # doctest: +ELLIPSIS
    now listening to catalog <zc.relation.catalog.Catalog object at ...>

    >>> catalog.clear() # doctest: +ELLIPSIS
    catalog <...Catalog...> had all relations unindexed

    >>> len(catalog)
    0
    >>> sorted(catalog.findValues(
    ...     'context',
    ...     (query(predicate=SELLS, object=doughnuts))),
    ...     key=lambda ob: ob.name)
    []

The ``copy`` Method
-------------------

Sometimes you may want to copy a relation catalog.  One way of doing this is
to create a new catalog, set it up like the current one, and then reindex
all the same relations.  This is unnecessarily slow for programmer and
computer.  The ``copy`` method makes a new catalog with the same corpus of
indexed relations by copying internal data structures.

Search indexes are requested to make new copies of themselves for the new
catalog; and listeners are given an opportunity to react as desired to the new
copy, including installing themselves, and/or another object of their choosing
as a listener.

Let's make a copy of a populated index with a search index and a listener.
Notice in our listener that ``sourceCopied`` adds itself as a listener to the
new copy. This is done at the very end of the ``copy`` process.

    >>> for r in (rel1, rel2, rel3, rel4, rel5):
    ...     catalog.index(r)
    ... # doctest: +ELLIPSIS
    a relation ... was added...
    a relation ... was added...
    a relation ... was added...
    a relation ... was added...
    a relation ... was added...
    >>> BEGAT = 'BEGAT'
    >>> rel6 = root['rel6'] = Relation((jack, ann), BEGAT, (sara,))
    >>> henry = root['henry'] = Demo('henry')
    >>> rel7 = root['rel7'] = Relation((sara, joe), BEGAT, (henry,))
    >>> catalog.index(rel6) # doctest: +ELLIPSIS
    a relation (token ...) was added to <...Catalog...> with these values:
    {'context': None,
     'object': set([...]),
     'predicate': set(['BEGAT']),
     'subject': set([..., ...])}
    >>> catalog.index(rel7) # doctest: +ELLIPSIS
    a relation (token ...) was added to <...Catalog...> with these values:
    {'context': None,
     'object': set([...]),
     'predicate': set(['BEGAT']),
     'subject': set([..., ...])}
    >>> catalog.addDefaultQueryFactory(
    ...     zc.relation.queryfactory.TransposingTransitive(
    ...         'subject', 'object', {'predicate': BEGAT}))
    ...
    >>> list(catalog.findValues(
    ...     'object', query(subject=jack, predicate=BEGAT)))
    [<Demo instance 'sara'>, <Demo instance 'henry'>]
    >>> catalog.addSearchIndex(
    ...     zc.relation.searchindex.TransposingTransitiveMembership(
    ...         'subject', 'object', static={'predicate': BEGAT}))
    >>> sorted(
    ...     catalog.findValues(
    ...         'object', query(subject=jack, predicate=BEGAT)),
    ...     key=lambda o: o.name)
    [<Demo instance 'henry'>, <Demo instance 'sara'>]

    >>> newcat = root['newcat'] = catalog.copy() # doctest: +ELLIPSIS
    catalog <...Catalog...> made a copy <...Catalog...>
    now listening to catalog <...Catalog...>
    >>> transaction.commit()

Now the copy has its own copies of internal data structures and of the
searchindex.  For example, let's modify the relations and add a new one to the
copy.

    >>> mary = root['mary'] = Demo('mary')
    >>> buffy = root['buffy'] = Demo('buffy')
    >>> zack = root['zack'] = Demo('zack')
    >>> rel7.objects += (mary,)
    >>> rel8 = root['rel8'] = Relation((henry, buffy), BEGAT, (zack,))
    >>> newcat.index(rel7) # doctest: +ELLIPSIS
    a relation (token ...) in ...Catalog... was modified with these additions:
    {'object': set([...])}
    and these removals:
    {}
    >>> newcat.index(rel8) # doctest: +ELLIPSIS
    a relation (token ...) was added to ...Catalog... with these values:
    {'context': None,
     'object': set([...]),
     'predicate': set(['BEGAT']),
     'subject': set([..., ...])}
    >>> len(newcat)
    8
    >>> sorted(
    ...     newcat.findValues(
    ...         'object', query(subject=jack, predicate=BEGAT)),
    ...     key=lambda o: o.name) # doctest: +NORMALIZE_WHITESPACE
    [<Demo instance 'henry'>, <Demo instance 'mary'>, <Demo instance 'sara'>,
     <Demo instance 'zack'>]
    >>> sorted(
    ...     newcat.findValues(
    ...         'object', query(subject=sara)),
    ...     key=lambda o: o.name) # doctest: +NORMALIZE_WHITESPACE
    [<Demo instance 'bistro'>, <Demo instance 'cookies'>,
    <Demo instance 'doughnuts'>, <Demo instance 'henry'>,
    <Demo instance 'mary'>, <Demo instance 'muffins'>]

The original catalog is not modified.

    >>> len(catalog)
    7
    >>> sorted(
    ...     catalog.findValues(
    ...         'object', query(subject=jack, predicate=BEGAT)),
    ...     key=lambda o: o.name)
    [<Demo instance 'henry'>, <Demo instance 'sara'>]
    >>> sorted(
    ...     catalog.findValues(
    ...         'object', query(subject=sara)),
    ...     key=lambda o: o.name) # doctest: +NORMALIZE_WHITESPACE
    [<Demo instance 'bistro'>, <Demo instance 'cookies'>,
     <Demo instance 'doughnuts'>, <Demo instance 'henry'>,
     <Demo instance 'muffins'>]

The ``ignoreSearchIndex`` argument
----------------------------------

The five methods that can use search indexes, ``findValues``,
``findValueTokens``, ``findRelations``, ``findRelationTokens``, and
``canFind``, can be explicitly requested to ignore any pertinent search index
using the ``ignoreSearchIndex`` argument.

We can see this easily with the token-related methods: the search index result
will be a BTree set, while without the search index the result will be a
generator.

    >>> res1 = newcat.findValueTokens(
    ...     'object', query(subject=jack, predicate=BEGAT))
    >>> res1 # doctest: +ELLIPSIS
    LFSet([..., ..., ..., ...])
    >>> res2 = newcat.findValueTokens(
    ...     'object', query(subject=jack, predicate=BEGAT),
    ...     ignoreSearchIndex=True)
    >>> res2 # doctest: +ELLIPSIS
    <generator object at 0x...>
    >>> sorted(res2) == list(res1)
    True

    >>> res1 = newcat.findRelationTokens(
    ...     query(subject=jack, predicate=BEGAT))
    >>> res1 # doctest: +ELLIPSIS
    LFSet([..., ..., ...])
    >>> res2 = newcat.findRelationTokens(
    ...     query(subject=jack, predicate=BEGAT), ignoreSearchIndex=True)
    >>> res2 # doctest: +ELLIPSIS
    <generator object at 0x...>
    >>> sorted(res2) == list(res1)
    True

We can see that the other methods take the argument, but the results look the
same as usual.

    >>> res = newcat.findValues(
    ...     'object', query(subject=jack, predicate=BEGAT),
    ...     ignoreSearchIndex=True)
    >>> res # doctest: +ELLIPSIS
    <generator object at 0x...>
    >>> list(res) == list(newcat.resolveValueTokens(newcat.findValueTokens(
    ...     'object', query(subject=jack, predicate=BEGAT),
    ...     ignoreSearchIndex=True), 'object'))
    True

    >>> res = newcat.findRelations(
    ...     query(subject=jack, predicate=BEGAT),
    ...     ignoreSearchIndex=True)
    >>> res # doctest: +ELLIPSIS
    <generator object at 0x...>
    >>> list(res) == list(newcat.resolveRelationTokens(
    ...     newcat.findRelationTokens(
    ...         query(subject=jack, predicate=BEGAT),
    ...         ignoreSearchIndex=True)))
    True

    >>> newcat.canFind(
    ...     query(subject=jack, predicate=BEGAT), ignoreSearchIndex=True)
    True

``findRelationTokens()``
------------------------

If you call ``findRelationTokens`` without any arguments, you will get the
BTree set of all relation tokens in the catalog.  This can be handy for tests
and for advanced uses of the catalog.

    >>> newcat.findRelationTokens() # doctest: +ELLIPSIS
    <BTrees.LFBTree.LFTreeSet object at ...>
    >>> len(newcat.findRelationTokens())
    8
    >>> set(newcat.resolveRelationTokens(newcat.findRelationTokens())) == set(
    ...     (rel1, rel2, rel3, rel4, rel5, rel6, rel7, rel8))
    True

``findValueTokens(INDEX_NAME)``
-------------------------------

If you call ``findValueTokens`` with only an index name, you will get the BTree
structure of all tokens for that value in the index. This can be handy for
tests and for advanced uses of the catalog.

    >>> newcat.findValueTokens('predicate') # doctest: +ELLIPSIS
    <BTrees.OOBTree.OOBTree object at ...>
    >>> list(newcat.findValueTokens('predicate'))
    ['BEGAT', 'BUYS', 'OBSERVES', 'SELLS']

Conclusion
==========

Review
------

That brings us to the end of our introductory examples.  Let's review, and
then look at where you can go from here.

* Relations are objects with indexed values.

* The relation catalog indexes relations. The relations can be one-way,
  two-way, three-way, or N-way, as long as you tell the catalog to index the
  different values.

* Creating a catalog:
    
    - Relations and their values are stored in the catalog as tokens: unique
      identifiers that you can resolve back to the original value. Integers are
      the most efficient tokens, but others can work fine too.
    
    - Token type determines the BTree module needed.
    
        - If the tokens are 32-bit ints, choose ``BTrees.family32.II``,
          ``BTrees.family32.IF`` or ``BTrees.family32.IO``.
        
        - If the tokens are 64 bit ints, choose ``BTrees.family64.II``,
          ``BTrees.family64.IF`` or ``BTrees.family64.IO``.
        
        - If they are anything else, choose ``BTrees.family32.OI``,
          ``BTrees.family64.OI``, or ``BTrees.family32.OO`` (or
          BTrees.family64.OO--they are the same).
        
      Within these rules, the choice is somewhat arbitrary unless you plan to
      merge these results with that of another source that is using a
      particular BTree module. BTree set operations only work within the same
      module, so you must match module to module.

    - The ``family`` argument in instantiating the catalog lets you change the
      default btree family for relations and value indexes from
      ``BTrees.family32.IF`` to ``BTrees.family64.IF``.

    - You must define your own functions for tokenizing and resolving tokens.
      These functions are registered with the catalog for the relations and for
      each of their value indexes.

    - You add value indexes to relation catalogs to be able to search.  Values
      can be identified to the catalog with callables or interface elements.
    
        - Using interface attributes will cause an attempt to adapt the
          relation if it does not already provide the interface.
        
        - We can use the ``multiple`` argument when defining a value index to
          indicate that the indexed value is a collection.  This defaults to
          False.
        
        - We can use the ``name`` argument when defining a value index to
          specify the name to be used in queries, rather than relying on the
          name of the interface attribute or callable.

    - You can set up search indexes to speed up specific searches, usually
      transitive.

    - Listeners can be registered in the catalog. They are alerted when a
      relation is added, modified, or removed; and when the catalog is cleared
      and copied.

* Catalog Management:

    - Relations are indexed with ``index(relation)``, and removed from the
      catalog with ``unindex(relation)``. ``index_doc(relation_token,
      relation)`` and ``unindex_doc(relation_token)`` also work.

    - The ``clear`` method clears the relations in the catalog.
    
    - The ``copy`` method makes a copy of the current catalog by copying
      internal data structures, rather than reindexing the relations, which can
      be a significant optimization opportunity. This copies value indexes and
      search indexes; and gives listeners an opportunity to specify what, if
      anything, should be included in the new copy.

* Searching a catalog:

    - Queries to the relation catalog are formed with dicts.
    
    - Query keys are the names of the indexes you want to search, or, for the
      special case of precise relations, the ``zc.relation.RELATION`` constant.
    
    - Query values are the tokens of the results you want to match; or
      ``None``, indicating relations that have ``None`` as a value (or an empty
      collection, if it is a multiple). Search values can use
      ``zc.relation.catalog.any(args)`` or ``zc.relation.catalog.Any(args)`` to
      specify multiple (non-``None``) results to match for a given key.

    - The index has a variety of methods to help you work with tokens.
      ``tokenizeQuery`` is typically the most used, though others are
      available.
    
    - To find relations that match a query, use ``findRelations`` or
      ``findRelationTokens``.  Calling ``findRelationTokens`` without any
      arguments returns the BTree set of all relation tokens in the catalog.
    
    - To find values that match a query, use ``findValues`` or
      ``findValueTokens``.  Calling ``findValueTokens`` with only the name
      of a value index returns the BTree set of all tokens in the catalog for
      that value index.
    
    - You search transitively by using a query factory. The
      ``zc.relation.queryfactory.TransposingTransitive`` is a good common case
      factory that lets you walk up and down a hierarchy. A query factory can
      be passed in as an argument to search methods as a ``queryFactory``, or
      installed as a default behavior using ``addDefaultQueryFactory``.
    
    - To find how a query is related, use ``findRelationChains`` or
      ``findRelationTokenChains``.
    
    - To find out if a query is related, use ``canFind``.
    
    - Circular transitive relations are handled to prevent infinite loops. They
      are identified in ``findRelationChains`` and ``findRelationTokenChains``
      with a ``zc.relation.interfaces.ICircularRelationPath`` marker interface.

    - search methods share the following arguments:
    
      * ``maxDepth``, limiting the transitive depth for searches;
      
      * ``filter``, allowing code to filter transitive paths;
      
      * ``targetQuery``, allowing a query to filter transitive paths on the
        basis of the endpoint;
      
      * ``targetFilter``, allowing code to filter transitive paths on the basis
        of the endpoint; and
    
      * ``queryFactory``, mentioned above.
      
      In addition, the ``ignoreSearchIndex`` argument to ``findRelations``,
      ``findRelationTokens``, ``findValues``, ``findValueTokens``, and
      ``canFind`` causes the search to ignore search indexes, even if there is
      an appropriate one.

Next Steps
----------

If you want to read more, next steps depend on how you like to learn.  Here
are some of the other documents in the zc.relation package.

:optimization.txt:
    Best practices for optimizing your use of the relation catalog.

:searchindex.txt:
    Queries factories and search indexes: from basics to nitty gritty details.

:tokens.txt:
    This document explores the details of tokens.  All God's chillun
    love tokens, at least if God's chillun are writing non-toy apps
    using zc.relation.  It includes discussion of the token helpers that
    the catalog provides, how to use zope.app.intid-like registries with
    zc.relation, how to use tokens to "join" query results reasonably
    efficiently, and how to index joins.  It also is unnecessarily
    mind-blowing because of the examples used.

:interfaces.py:
    The contract, for nuts and bolts.

Finally, the truly die-hard might also be interested in the timeit
directory, which holds scripts used to test assumptions and learn.

.. ......... ..
.. FOOTNOTES ..
.. ......... ..

.. [#verifyObjectICatalog] The catalog provides ICatalog.

    >>> from zope.interface.verify import verifyObject
    >>> import zc.relation.interfaces
    >>> verifyObject(zc.relation.interfaces.ICatalog, catalog)
    True

.. [#legacy] Old instances of zc.relationship indexes, which in the newest
    version subclass a zc.relation Catalog, used to have a dict in an
    internal data structure.  We specify that here so that the code that
    converts the dict to an OOBTree can have a chance to run.

    >>> catalog._attrs = dict(catalog._attrs)

.. [#addValueIndexExceptions] Adding a value index can generate several
    exceptions.
    
    You must supply both of dump and load or neither.

    >>> catalog.addValueIndex(supervisor, dumpEmployees, None,
    ...                       btree=BTrees.family32.OI, name='supervisor2')
    Traceback (most recent call last):
    ...
    ValueError: either both of 'dump' and 'load' must be None, or neither

    In this example, even if we fix it, we'll get an error, because we have
    already indexed the supervisor function.

    >>> catalog.addValueIndex(supervisor, dumpEmployees, loadEmployees,
    ...                       btree=BTrees.family32.OI, name='supervisor2')
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: ('element already indexed', <function supervisor at ...>)

    You also can't add a different function under the same name.
    
    >>> def supervisor2(emp, catalog):
    ...     return emp.supervisor # None or another employee
    ...
    >>> catalog.addValueIndex(supervisor2, dumpEmployees, loadEmployees,
    ...                       btree=BTrees.family32.OI, name='supervisor')
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: ('name already used', 'supervisor')

    Finally, if your function does not have a ``__name__`` and you do not
    provide one, you may not add an index.
    
    >>> class Supervisor3(object):
    ...     __name__ = None
    ...     def __call__(klass, emp, catalog):
    ...         return emp.supervisor
    ...
    >>> supervisor3 = Supervisor3()
    >>> supervisor3.__name__
    >>> catalog.addValueIndex(supervisor3, dumpEmployees, loadEmployees,
    ...                       btree=BTrees.family32.OI)
    ... # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: no name specified

.. [#any] ``Any`` can be compared.

    >>> zc.relation.catalog.any('foo', 'bar', 'baz')
    <zc.relation.catalog.Any instance ('bar', 'baz', 'foo')>
    >>> (zc.relation.catalog.any('foo', 'bar', 'baz') ==
    ...  zc.relation.catalog.any('bar', 'foo', 'baz'))
    True
    >>> (zc.relation.catalog.any('foo', 'bar', 'baz') !=
    ...  zc.relation.catalog.any('bar', 'foo', 'baz'))
    False
    >>> (zc.relation.catalog.any('foo', 'bar', 'baz') ==
    ...  zc.relation.catalog.any('foo', 'baz'))
    False
    >>> (zc.relation.catalog.any('foo', 'bar', 'baz') !=
    ...  zc.relation.catalog.any('foo', 'baz'))
    True

.. [#intrinsic_search] Here's the same with token results.

    >>> list(catalog.findValueTokens('supervisor',
    ...                              {zc.relation.RELATION: 'Howie'}))
    ['Diane']

    While we're down here in the footnotes, I'll mention that you can
    search for relations that haven't been indexed.

    >>> list(catalog.findRelationTokens({zc.relation.RELATION: 'Ygritte'}))
    []
    >>> list(catalog.findRelations({zc.relation.RELATION: 'Ygritte'}))
    []

.. [#findValuesExceptions] If you use ``findValues`` or ``findValueTokens`` and
    try to specify a value name that is not indexed, you get a ValueError.
    
    >>> catalog.findValues('foo')
    Traceback (most recent call last):
    ...
    ValueError: ('name not indexed', 'foo')

.. [#I_care] OK, you care about how that query factory worked, so
    we will look into it a bit.  Let's talk through two steps of the
    transitive search in the second question.  The catalog initially
    performs the initial intransitive search requested: find relations
    for which Betty is the supervisor.  That's Diane and Edgar. 
    
    Now, for each of the results, the catalog asks the query factory for
    next steps.  Let's take Diane.  The catalog says to the factory,
    "Given this query for relations where Betty is supervisor, I got
    this result of Diane.  Do you have any other queries I should try to
    look further?".  The factory also gets the catalog instance so it
    can use it to answer the question if it needs to.

    OK, the next part is where your brain hurts.  Hang on.
    
    In our case, the factory sees that the query was for supervisor. Its
    other key, the one it transposes with, is ``zc.relation.RELATION``. *The
    factory gets the transposing key's result for the current token.* So, for
    us, a key of ``zc.relation.RELATION`` is actually a no-op: the result *is*
    the current token, Diane. Then, the factory has its answer: replace the old
    value of supervisor in the query, Betty, with the result, Diane. The next
    transitive query should be {'supervisor', 'Diane'}. Ta-da.

.. [#needs_a_transitive_queries_factory] A search with a ``maxDepth`` > 1 but
    no ``queryFactory`` raises an error.
    
    >>> catalog.removeDefaultQueryFactory(factory)
    >>> catalog.findRelationTokens({'supervisor': 'Diane'}, maxDepth=3)
    Traceback (most recent call last):
    ...
    ValueError: if maxDepth not in (None, 1), queryFactory must be available

    >>> catalog.addDefaultQueryFactory(factory)

.. [#maxDepthExceptions] ``maxDepth`` must be None or a positive integer, or
    else you'll get a value error.
    
    >>> catalog.findRelations({'supervisor': 'Betty'}, maxDepth=0)
    Traceback (most recent call last):
    ...
    ValueError: maxDepth must be None or a positive integer

    >>> catalog.findRelations({'supervisor': 'Betty'}, maxDepth=-1)
    Traceback (most recent call last):
    ...
    ValueError: maxDepth must be None or a positive integer

.. [#filter] For instance:

    >>> list(catalog.findRelationTokens(
    ...     {'supervisor': 'Alice'}, targetFilter=female_filter,
    ...     targetQuery={zc.relation.RELATION: 'Galyn'}))
    ['Galyn']
    >>> list(catalog.findRelationTokens(
    ...     {'supervisor': 'Alice'}, targetFilter=female_filter,
    ...     targetQuery={zc.relation.RELATION: 'Not known'}))
    []
    >>> arbitrary = ['Alice', 'Chuck', 'Betty', 'Galyn']
    >>> def arbitrary_filter(relchain, query, catalog, cache):
    ...     return relchain[-1] in arbitrary
    >>> list(catalog.findRelationTokens({'supervisor': 'Alice'},
    ...                                 filter=arbitrary_filter,
    ...                                 targetFilter=female_filter))
    ['Betty', 'Galyn']

.. [#updates] The scenario we are looking at in this document shows a case
    in which special logic in the search index needs to address updates.
    For example, if we move Howie from Diane

    ::

                 Alice
              __/     \__
         Betty           Chuck
         /   \           /   \
     Diane   Edgar   Frank   Galyn
       |
     Howie

    to Galyn

    ::

                 Alice
              __/     \__
         Betty           Chuck
         /   \           /   \
     Diane   Edgar   Frank   Galyn
                               |
                             Howie

    then the search index is correct both for the new location and the old.

    >>> h.supervisor = g
    >>> catalog.index(h)
    >>> list(catalog.findRelationTokens({'supervisor': 'Diane'}))
    []
    >>> list(catalog.findRelationTokens({'supervisor': 'Betty'}))
    ['Diane', 'Edgar']
    >>> list(catalog.findRelationTokens({'supervisor': 'Chuck'}))
    ['Frank', 'Galyn', 'Howie']
    >>> list(catalog.findRelationTokens({'supervisor': 'Galyn'}))
    ['Howie']
    >>> h.supervisor = d
    >>> catalog.index(h) # move him back
    >>> list(catalog.findRelationTokens({'supervisor': 'Galyn'}))
    []
    >>> list(catalog.findRelationTokens({'supervisor': 'Diane'}))
    ['Howie']

.. [#same_set] The result of the query for Betty, Alice, and Zane are all the
    same.

    >>> res1 = catalog.findRelationTokens({'supervisor': 'Betty'})
    >>> res2 = catalog.findRelationTokens({'supervisor': 'Alice'})
    >>> res3 = catalog.findRelationTokens({'supervisor': 'Zane'})
    >>> list(res1) == list(res2) == list(res3)
    True

    The cycle doesn't pollute the index outside of the cycle.
    
    >>> res = catalog.findRelationTokens({'supervisor': 'Diane'})
    >>> list(res)
    ['Howie']
    >>> list(res) # it isn't lazy, it is precalculated
    ['Howie']

.. [#reverse_lookup] If you want to, look what happens when you go the
    other way:

    >>> res = list(catalog.findRelationChains({'supervisor': 'Zane'}))
    >>> def sortEqualLenByName(one, two):
    ...     if len(one) == len(two):
    ...         return cmp(one, two)
    ...     return 0
    ...
    >>> res.sort(sortEqualLenByName) # normalizes for test stability
    >>> print res # doctest: +NORMALIZE_WHITESPACE
    [(<Employee instance "Alice">,),
     (<Employee instance "Alice">, <Employee instance "Betty">),
     (<Employee instance "Alice">, <Employee instance "Chuck">),
     (<Employee instance "Alice">, <Employee instance "Betty">,
      <Employee instance "Diane">),
     (<Employee instance "Alice">, <Employee instance "Betty">,
      <Employee instance "Edgar">),
     cycle(<Employee instance "Alice">, <Employee instance "Betty">,
           <Employee instance "Zane">),
     (<Employee instance "Alice">, <Employee instance "Chuck">,
      <Employee instance "Frank">),
     (<Employee instance "Alice">, <Employee instance "Chuck">,
      <Employee instance "Galyn">),
     (<Employee instance "Alice">, <Employee instance "Betty">,
      <Employee instance "Diane">, <Employee instance "Howie">)]

    >>> [zc.relation.interfaces.ICircularRelationPath.providedBy(r)
    ...  for r in res]
    [False, False, False, False, False, True, False, False, False]
    >>> len(res[5].cycled)
    1
    >>> list(catalog.findRelations(res[5].cycled[0], maxDepth=1))
    [<Employee instance "Alice">]
