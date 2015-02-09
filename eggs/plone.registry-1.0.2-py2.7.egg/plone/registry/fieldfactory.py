import zope.interface
import zope.component

import plone.registry.field

from zope.schema.interfaces import IField, IChoice
from zope.schema.interfaces import ISource, IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary

from plone.registry.interfaces import IPersistentField
from plone.registry.field import DisallowedProperty, StubbornProperty, InterfaceConstrainedProperty
from plone.registry.field import is_primitive


@zope.interface.implementer(IPersistentField)
@zope.component.adapter(IField)
def persistentFieldAdapter(context):
    """Turn a non-persistent field into a persistent one
    """

    if IPersistentField.providedBy(context):
        return context

    # See if we have an equivalently-named field

    class_name = context.__class__.__name__
    persistent_class = getattr(plone.registry.field, class_name, None)
    if persistent_class is None:
        return None

    if not issubclass(persistent_class, context.__class__):
        __traceback_info__ = "Can only clone a field of an equivalent type."
        return None

    ignored = list(DisallowedProperty.uses + StubbornProperty.uses)
    constrained = list(InterfaceConstrainedProperty.uses)

    instance = persistent_class.__new__(persistent_class)

    context_dict = dict([(k,v) for k,v in context.__dict__.items()
                            if k not in ignored])

    for k,iface in constrained:
        v = context_dict.get(k, None)
        if v is not None and v != context.missing_value:
            v = iface(v, None)
            if v is None:
                __traceback_info__ = "The property `%s` cannot be adapted to `%s`." % (k, iface.__identifier__,)
                return None
            context_dict[k] = v

    instance.__dict__.update(context_dict)
    return instance

@zope.interface.implementer(IPersistentField)
@zope.component.adapter(IChoice)
def choicePersistentFieldAdapter(context):
    """Special handling for Choice fields.
    """

    instance = persistentFieldAdapter(context)
    if instance is None:
        return None

    if ISource.providedBy(context.vocabulary) or \
            IContextSourceBinder.providedBy(context.vocabulary):

        safe = False

        # Attempt to reverse engineer a 'values' argument
        if isinstance(context.vocabulary, SimpleVocabulary):
            values = []
            safe = True
            for term in context.vocabulary:
                if term.token == str(term.value) and is_primitive(term.value):
                    values.append(term.value)
                else:
                    safe = False
                    break
            if safe:
                instance._values = values

        if not safe:
            __traceback_info__ = "Persistent fields only support named vocabularies " + \
                                    "or vocabularies based on simple value sets."
            return None

    return instance