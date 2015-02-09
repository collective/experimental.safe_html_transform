from zope.event import notify
from wicked.fieldevent.interfaces import IFieldEvent, IFieldRenderEvent, IFieldStorageEvent
from wicked.fieldevent.interfaces import IFieldValue, IFieldValueSetter, IField
from wicked.fieldevent.interfaces import FieldRenderEvent, FieldStorageEvent
from zope.component import subscribers, getMultiAdapter, handle
from zope.component import adapter, adapts
from zope.interface import implementer, implements

import logging
logger = logging.getLogger('wicked.fieldevent')

@adapter(IFieldEvent)
def notifyFieldEvent(event):
    field = event.field
    if IFieldRenderEvent.providedBy(event):
        event.value = getMultiAdapter((field, event), IFieldValue)
        if event.kwargs.get('raw', False) or getattr(event, 'raw', False):
            # bail out
            return

    handle(event.field, event.instance, event)

    if IFieldStorageEvent.providedBy(event):
        for ignore in subscribers((field, event), IFieldValueSetter):
            pass

def render(field_, instance, **kwargs):
    renderer=FieldRenderEvent(field_, instance, **kwargs)
    notify(renderer)
    return renderer.value

def store(field_, instance, value, **kwargs):
    store = FieldStorageEvent(field_, instance, value, **kwargs)
    notify(store)

# @@ separate IATField interfaces?
@implementer(IFieldValue)
@adapter(IField, IFieldRenderEvent)
def at_field_retrieval(field, event):
    return field.get(event.instance, **event.kwargs)

# @@ separate IATField interfaces?
@implementer(IFieldValueSetter)
@adapter(IField, IFieldStorageEvent)
def at_field_storage(field, event):
    field.set(event.instance, event.value, **event.kwargs)

## testing! ##

def test_suite():
    import unittest
    from zope.testing import doctest
    from zope.component import provideAdapter, provideHandler
    from zope.component import provideSubscriptionAdapter
    from zope.testing.cleanup import cleanUp

    def setUp(tc):
        # clean slate!
        cleanUp()

        # init event system
        from zope.component import event

        # register components
        provideHandler(notifyFieldEvent)
        provideAdapter(at_field_retrieval)
        provideSubscriptionAdapter(at_field_storage)

    def tearDown(tc):
        cleanUp()

    globs=globals()
    globs.update(locals())

    optflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
    rm = doctest.DocFileTest("README.txt",
                             package="wicked.fieldevent",
                             globs=globs,
                             setUp=setUp,
                             tearDown=tearDown,
                             optionflags=optflags)

    return unittest.TestSuite((rm,))
