from plone.supermodel.exportimport import BaseHandler, DictHandler, ChoiceHandler
from plone.registry import field


class PersistentFieldHandler(BaseHandler):
    filteredAttributes = BaseHandler.filteredAttributes.copy()
    filteredAttributes.update({'interfaceName': 'rw', 'fieldName': 'rw'})


class PersistentDictHandler(DictHandler):
    filteredAttributes = DictHandler.filteredAttributes.copy()
    filteredAttributes.update({'interfaceName': 'rw', 'fieldName': 'rw'})


class PersistentChoiceHandler(ChoiceHandler):
    filteredAttributes = ChoiceHandler.filteredAttributes.copy()
    filteredAttributes.update({'interfaceName': 'rw', 'fieldName': 'rw'})

# Field import/export handlers

BytesHandler = PersistentFieldHandler(field.Bytes)
BytesLineHandler = PersistentFieldHandler(field.BytesLine)

ASCIIHandler = PersistentFieldHandler(field.ASCII)
ASCIILineHandler = PersistentFieldHandler(field.ASCIILine)

TextHandler = PersistentFieldHandler(field.Text)
TextLineHandler = PersistentFieldHandler(field.TextLine)

PasswordHandler = PersistentFieldHandler(field.Password)
SourceTextHandler = PersistentFieldHandler(field.SourceText)

DottedNameHandler = PersistentFieldHandler(field.DottedName)
URIHandler = PersistentFieldHandler(field.URI)
IdHandler = PersistentFieldHandler(field.Id)

BoolHandler = PersistentFieldHandler(field.Bool)
IntHandler = PersistentFieldHandler(field.Int)
FloatHandler = PersistentFieldHandler(field.Float)

DatetimeHandler = PersistentFieldHandler(field.Datetime)
DateHandler = PersistentFieldHandler(field.Date)

TupleHandler = PersistentFieldHandler(field.Tuple)
ListHandler = PersistentFieldHandler(field.List)
SetHandler = PersistentFieldHandler(field.Set)
FrozenSetHandler = PersistentFieldHandler(field.FrozenSet)

DictHandler = PersistentDictHandler(field.Dict)

ChoiceHandler = PersistentChoiceHandler(field.Choice)
