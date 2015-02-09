from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import XMLAdapterBase

from Products.CMFCore.utils import getToolByName

from Products.PloneLanguageTool.interfaces import ILanguageTool

class LanguageToolXMLAdapter(XMLAdapterBase):

    __used_for__ = ILanguageTool

    _LOGGER_ID = 'portal_languages'

    name = 'portal_languages'

    boolean_fields =  [ "use_path_negotiation", "use_cookie_negotiation",
                        "set_cookie_everywhere",
                        "use_request_negotiation", "use_cctld_negotiation",
                        "use_content_negotiation",
                        "use_combined_language_codes", "display_flags",
                        "start_neutral", "use_subdomain_negotiation",
                        "authenticated_users_only" ]
    list_fields = [ "supported_langs" ]

    def _exportNode(self):
        """Export the object as a DOM node"""

        node=self._extractProperties()
        self._logger.info('Plone language tool exported.')

        return node

    def _importNode(self, node):
        """Import the object from the DOM node"""

        if self.environ.shouldPurge():
            self._purgeProperties()

        self._initProperties(node)

        self._logger.info('Plone language tool imported.')

    def _purgeProperties(self):
        self.context.supported_langs = [ 'en' ]
        self.context.use_content_negotiation = 0
        self.context.use_path_negotiation = 0
        self.context.use_cookie_negotiation = 1
        self.context.authenticated_users_only = 0
        self.context.use_request_negotiation = 1
        self.context.use_cctld_negotiation = 0
        self.context.use_subdomain_negotiation = 0
        self.context.use_combined_language_codes = 0
        self.context.display_flags = 0
        self.context.start_neutral = 0
        self.context.setDefaultLanguage("en")

    def _initProperties(self, node):
        for child in node.childNodes:
            if child.nodeName in self.boolean_fields:
                value = self._convertToBoolean(child.getAttribute('value'))
                setattr(self.context, child.nodeName, value)
            elif child.nodeName in self.list_fields:
                purge = self._convertToBoolean(child.getAttribute('purge') or 'True')
                if purge:
                    value = []
                else:
                    value = getattr(self.context, child.nodeName)
                for element in child.childNodes:
                    if element.nodeName=='element':
                        value.append(str(element.getAttribute('value')))
                setattr(self.context, child.nodeName, value)
            elif child.nodeName=='default_language':
                self.context.setDefaultLanguage(str(child.getAttribute('value')))

    def _extractProperties(self):
        node=self._doc.createElement('object')
        child=self._doc.createElement('default_language')
        child.setAttribute('value', self.context.getDefaultLanguage())
        node.appendChild(child)

        for field in self.boolean_fields:
            child=self._doc.createElement(field)
            child.setAttribute('value', str(bool(getattr(self.context, field))))
            node.appendChild(child)

        for field in self.list_fields:
            child=self._doc.createElement(field)
            value=getattr(self.context, field)
            for item in value:
                element = self._doc.createElement('element')
                element.setAttribute('value', item)
                child.appendChild(element)
            node.appendChild(child)

        return node



def importLanguageTool(context):
    """Import Plone language tool settings from an XML file.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_languages')

    importObjects(tool, '', context)

def exportLanguageTool(context):
    """Export Plone language tool settings as an XML file.
    """
    site = context.getSite()
    tool = getToolByName(site, 'portal_languages', None)
    if tool is None:
        logger = context.getLogger('portal_languages')
        logger.info('Nothing to export.')
        return

    exportObjects(tool, '', context)


