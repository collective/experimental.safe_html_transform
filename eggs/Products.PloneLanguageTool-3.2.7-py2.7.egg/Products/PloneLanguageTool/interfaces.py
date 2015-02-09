from zope.interface import Interface, Attribute

try:
    from Products.LinguaPlone.interfaces import ITranslatable
except ImportError:
    class ITranslatable(Interface):
        pass

class ILanguageTool(Interface):
    """Marker interface for the portal_languages tool.
    """

class INegotiateLanguage(Interface):
    """Result of language negotiation
    """
    language = Attribute('Language to use')
    default_language = Attribute('Default language')
    language_list = Attribute('List of language preferences in order')
