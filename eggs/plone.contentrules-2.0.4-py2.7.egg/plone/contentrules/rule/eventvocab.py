from zope.interface import Interface, classProvides
from zope.interface.interfaces import IInterface
import zope.component
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.i18nmessageid import MessageFactory

from zope.componentvocabulary.vocabulary import UtilityVocabulary

from plone.contentrules.rule.interfaces import IRuleEventType


_ = MessageFactory('plone')

class EventTypesVocabulary(UtilityVocabulary):
    """A vocabulary for event interfaces that can be selected for the 'event'
    attribute of an IRule.
    An internationalized version of UtilityVocabulary
    """
    interface = IRuleEventType
    classProvides(IVocabularyFactory)

    def __init__(self, context, **kw):
        if kw:
            self.nameOnly = bool(kw.get('nameOnly', False))
            interface = kw.get('interface', Interface)
            if isinstance(interface, (str, unicode)):
                interface = zope.component.getUtility(IInterface, interface)
            self.interface = interface

        utils = zope.component.getUtilitiesFor(self.interface, context)
        self._terms = dict(
            (name, SimpleTerm(self.nameOnly and name or util, name, _(name)))
            for name, util in utils)
