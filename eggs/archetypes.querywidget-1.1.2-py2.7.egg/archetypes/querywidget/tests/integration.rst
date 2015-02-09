archetypes.querywidget
======================

Overall Integration
-------------------

This package contains the archetypes field and widget used in
plone.app.collection to select the search criteria of the collection.

First login as portal owner::

    >>> app = self.layer['app']
    >>> from plone.testing.z2 import Browser
    >>> browser = Browser(app)
    >>> browser.handleErrors = False
    >>> browser.addHeader('Authorization', 'Basic admin:secret')

We added a collection in the test layer, so we check if the query field
is there, and see if it's rendered::

    >>> portal = self.layer['portal']
    >>> field = portal.collection.getField('query')
    >>> from archetypes.querywidget.field import QueryField
    >>> isinstance(field, QueryField)
    True
    >>> browser.open(portal.collection.absolute_url()+'/edit')
    >>> 'id="archetypes-fieldname-query"' in browser.contents
    True
    >>> 'class="field ArchetypesQueryWidget' in browser.contents
    True

Bug Checks
----------

Check for bug `#13144 <https://dev.plone.org/ticket/13144>`_::

    >>> field = portal.collection.getField('query')
    >>> field.set(portal.collection, [{'i': 'start', 'o': 'some.namespace.op.foo'}])
    >>> raw1 = field.get(portal.collection, raw=True)
    >>> raw1
    [{'i': 'start', 'o': 'some.namespace.op.foo'}]

    >>> length1 = len(raw1)
    >>> raw1.append({'i': 'end', 'o': 'some.namespace.op.bar'})
    >>> raw2 = field.get(portal.collection, raw=True)

Now the amount of entries in raw2 has to be the same as in raw1::

    >>> length1 == len(raw2)
    True
