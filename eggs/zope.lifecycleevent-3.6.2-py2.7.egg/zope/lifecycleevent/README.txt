=================
Life-cycle events
=================

In Zope, events are used by components to inform each other about
relevant new objects and object modifications.

To keep all subscribers up to date it is indispensable that the life
cycle of an object is accompanied by various events.

    >>> from zope.event import notify
    >>> from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent

    >>> class Sample(object) :
    ...    "Test class"

    >>> obj = Sample()
    >>> notify(ObjectCreatedEvent(obj))
    
    >>> obj.modified = True
    >>> notify(ObjectModifiedEvent(obj))

Some event consumers like catalogs and caches may need more information to
update themselves in an efficient manner. The necessary information can be
provided as optional modification descriptions of the ObjectModifiedEvent.

Some examples:

    >>> from zope.interface import Interface, Attribute, implements
    >>> class IFile(Interface):
    ...     data = Attribute("Data")
    ... 

    >>> class File(object):
    ...     implements(IFile)
    ...

    >>> file = File()
    >>> file.data = "123"
    >>> notify(ObjectModifiedEvent(obj, IFile))

This says that we modified something via IFile. Note that an interface is an
acceptable description. In fact, we might allow pretty much anything as a
description and it depends on your needs what kind of descriptions you use.
