from wicked.fieldevent import render, store
from zope.interface import Interface, implementer
from zope.interface import noLongerProvides, alsoProvides
from zope.component import adapter
from zope.component.interface import provideInterface
from wicked.fieldevent.interfaces import IFieldValue
from wicked.fieldevent.interfaces import IFieldValueSetter
import itertools
import zope.component.zcml
from zope.configuration import fields
import zope.interface
import zope.schema
import wicked.fieldevent
from zope.component import provideAdapter, provideHandler
from zope.component import provideSubscriptionAdapter


class NewLineTokens(fields.Tokens):
    """ token field that splits on newline not space """

    def fromUnicode(self, u):
        u = u.strip()
        if u:
            vt = self.value_type.bind(self.context)
            values = []
            for s in u.split('\\n'):
                try:
                    v = vt.fromUnicode(s)
                except zope.schema.ValidationError, v:
                    raise fields.InvalidToken("%s in %s" % (v, u))
                else:
                    values.append(v)
        else:
            values = []

        self.validate(values)
        return values


class IATFieldDecoratorDirective(Interface):
    fieldclass = fields.GlobalObject(
        title=u"Field Class",
        required=True
        )

class IATSchemaFieldsImplementDirective(Interface):
    atclass = fields.GlobalObject(
        title=u"Archetypes Schema Object",
        required=True
        )

    implements = fields.GlobalObject(
        title=u"Archetypes Schema Object",
        required=True
        )

    fields = NewLineTokens(
        title=u"Names of fields to be marked",
        description=u"""
        Each field enumerated here will now directly provide the
        interfaces in implements.
        """,
        required=True,
        value_type=zope.schema.TextLine(missing_value=str()))


def decorate_at_field(_context=None, fieldclass=None, zcml=True):
    if not fieldclass in _fieldclass_monkies:

        # register adapters to call original methods

        _get=fieldclass.get
        _set=fieldclass.set

        @implementer(IFieldValue)
        @adapter(fieldclass, wicked.fieldevent.IFieldRenderEvent)
        def field_value(field, event):
            return _get(field, event.instance, **event.kwargs)

        @implementer(IFieldValueSetter)
        @adapter(fieldclass, wicked.fieldevent.IFieldStorageEvent)
        def field_value_set(field, event):
            _set(field, event.instance, event.value, **event.kwargs)

        if zcml:
            # do proper zopeish config
            zope.component.zcml.adapter(_context, (field_value,))
            zope.component.zcml.subscriber(_context,
                                           factory=field_value_set,
                                           provides=IFieldValueSetter)
            _context.action(
                discriminator = (fieldclass, monkey_getset),
                callable = monkey_getset,
                args = (fieldclass,)
                )
        else:
            # hook it up no delay
            monkey_getset(fieldclass)
            provideAdapter(field_value)
            provideSubscriptionAdapter(field_value_set)


_fieldclass_monkies=[]
def monkey_getset(fieldclass):
    global _fieldclass_monkies
    _get=fieldclass.get
    _set=fieldclass.set
    fieldclass.set = store
    fieldclass.get = render
    fieldclass.__original_get=_get
    fieldclass.__original_set=_set
    _fieldclass_monkies.append(fieldclass)


def schemafields_implement(_context=None, atclass=None, implements=None, fields=[], zcml=True):
    if zcml:
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = ('', implements)
            )
    schemafields_provide(implements, atclass.schema, fields)


_schemafields_marked=[]
def schemafields_provide(implements, schema, fieldnames, cleanup=False):
    action = noLongerProvides
    if not cleanup:
        global _schemafields_marked
        if (implements, schema, fieldnames) in _schemafields_marked:
            return
        _schemafields_marked.append((implements, schema, fieldnames))
        action = alsoProvides

    for name in fieldnames:
        field=schema[name]
        try:
            action(field, implements)
        except ValueError:
            pass


def cleanup_schemafields_provide():
    global _schemafields_marked
    for implements, schema, fieldnames in _schemafields_marked:
        schemafields_provide(implements, schema, fieldnames, cleanup=True)
    _schemafields_marked=[]


def cleanup_decorate_at_field():
    # unmonkey!
    global _fieldclass_monkies
    for class_ in _fieldclass_monkies:
        class_.get = class_.__original_get
        class_.set = class_.__original_set
    _fieldclass_monkies = []


def cleanUp():
    cleanup_decorate_at_field()
    cleanup_schemafields_provide()


from zope.testing.cleanup import addCleanUp
addCleanUp(cleanUp)
del addCleanUp


def test_suite():
    import unittest
    from zope.testing import doctest
    from zope.testing.cleanup import cleanUp

    def setUp(tc):
        # clean slate!
        cleanUp()
        provideHandler(wicked.fieldevent.notifyFieldEvent)

    def tearDown(tc):
        cleanUp()

    globs=globals()
    globs.update(locals())

    optflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
    meta = doctest.DocFileTest("meta.txt",
                             package="wicked.fieldevent",
                             globs=globs,
                             setUp=setUp,
                             tearDown=tearDown,
                             optionflags=optflags)

    return unittest.TestSuite((meta,))
