from zope.interface import implements, alsoProvides
from zope.schema.vocabulary import SimpleTerm
from plone.app.vocabularies.interfaces import IBrowsableTerm
from plone.app.vocabularies.interfaces import ITermWithDescription


class TermWithDescription(SimpleTerm):
    """
      >>> term = TermWithDescription('value', 'token', 'title')
      >>> term.value, term.token, term.title, term.description
      ('value', 'token', 'title', None)

      >>> term = TermWithDescription('value', 'token', 'title',
      ...                            description='description')
      >>> term.value, term.token, term.title, term.description
      ('value', 'token', 'title', 'description')
    """
    implements(ITermWithDescription)

    def __init__(self, value, token, title, description=None):
        super(TermWithDescription, self).__init__(value, token=token, title=title)
        self.description = description


class BrowsableTerm(TermWithDescription):
    """
      >>> term = BrowsableTerm('value')
      >>> term.value, term.token, term.title, term.description
      ('value', 'value', None, None)
      >>> IBrowsableTerm.providedBy(term)
      False

      >>> term = BrowsableTerm('value', 'token', 'title',
      ...                      description='description',
      ...                      browse_token='browse_token',
      ...                      parent_token='parent_token')
      >>> term.value, term.token, term.title, term.description
      ('value', 'token', 'title', 'description')
      >>> term.browse_token, term.parent_token
      ('browse_token', 'parent_token')
      >>> IBrowsableTerm.providedBy(term)
      True
    """

    def __init__(self, value, token=None, title=None, description=None,
                 browse_token=None, parent_token=None):
        super(BrowsableTerm, self).__init__(value, token=token,
                                            title=title, description=description)
        self.browse_token = browse_token
        self.parent_token = parent_token
        if browse_token is not None or parent_token is not None:
            alsoProvides(self, IBrowsableTerm)
