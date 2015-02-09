from zope.interface import implements
from Products.Archetypes import atapi

from archetypes.schemaextender.interfaces import IExtensionField
from archetypes.schemaextender.interfaces import ITranslatableExtensionField

HAS_LP = True
try:
    from Products.LinguaPlone.interfaces import ITranslatable
    from Products.LinguaPlone.utils import generatedMutatorWrapper
except ImportError:
    HAS_LP = False


class BaseExtensionField(object):
    """Mix-in class to make Archetypes fields not depend on generated
    accessors and mutators, and use AnnotationStorage by default.

    See README.txt for more information.
    """

    implements(IExtensionField)

    storage = atapi.AnnotationStorage()

    def getAccessor(self, instance):
        def accessor(**kw):
            return self.get(instance, **kw)
        return accessor

    def getEditAccessor(self, instance):
        if not hasattr(self, 'getRaw'):
            return None
        def edit_accessor(**kw):
            return self.getRaw(instance, **kw)
        return edit_accessor

    def getMutator(self, instance):
        def mutator(value, **kw):
            self.set(instance, value, **kw)
        return mutator

    def getIndexAccessor(self, instance):
        name = getattr(self, 'index_method', None)
        if name is None or name == '_at_accessor':
            return self.getAccessor(instance)
        elif name == '_at_edit_accessor':
            return self.getEditAccessor(instance)
        elif not isinstance(name, basestring):
            raise ValueError('Bad index accessor value: %r', name)
        else:
            return getattr(instance, name)


class TranslatableExtensionField(BaseExtensionField):
    """Extension field for a translatable content item.

    Needs to copy the language-independant values across translations.
    """
    implements(ITranslatableExtensionField)

    def getMutator(self, instance):
        name = self.getName()
        generatedMutator = generatedMutatorWrapper(name)
        def mutator(value, **kw):
            if (not ITranslatable.providedBy(instance) or
                not self.languageIndependent):
                return self.getTranslationMutator(instance)(value, **kw)
            # Use the generatedMutator from LinguaPlone
            return generatedMutator(instance, value, **kw)
        return mutator

    def getTranslationMutator(self, instance):
        """Return a mutator for translatable values"""
        def mutator(value, **kw):
            return self.set(instance, value, **kw)
        return mutator

    def isLanguageIndependent(self, instance):
        """Get the language independed flag for i18n content."""
        return self.languageIndependent


# We support LinguaPlone implicitly in the same way Archetypes does.
if HAS_LP:
    ExtensionField = TranslatableExtensionField
else:
    ExtensionField = BaseExtensionField

__all__ = (ExtensionField, )
