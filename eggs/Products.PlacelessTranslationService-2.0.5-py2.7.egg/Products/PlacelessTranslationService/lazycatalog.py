from zope.i18n.gettextmessagecatalog import GettextMessageCatalog
from zope.i18n.gettextmessagecatalog import _KeyErrorRaisingFallback


class LazyGettextMessageCatalog(GettextMessageCatalog):
    """A gettext message catalog which doesn't parse the files until they
       are accessed first.
    """

    def __init__(self, language, domain, path_to_file):
        """Initialize the message catalog"""
        self.language = language
        self.domain = domain
        self._path_to_file = path_to_file
        self._catalog = None

    def _check_reload(self):
        if self._catalog is None:
            self.reload()
            if not self._catalog._fallback:
                self._catalog.add_fallback(_KeyErrorRaisingFallback())

    def getMessage(self, id):
        'See IMessageCatalog'
        self._check_reload()
        return self._catalog.ugettext(id)

    def queryMessage(self, id, default=None):
        'See IMessageCatalog'
        self._check_reload()
        try:
            return self._catalog.ugettext(id)
        except KeyError:
            return default
