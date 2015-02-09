try:
    from Products.CMFPlone.interfaces.syndication import ISyndicatable
except ImportError:
    from zope.interface import Interface as ISyndicatable


class ICollection(ISyndicatable):
    """ Collection marker interface
    """
