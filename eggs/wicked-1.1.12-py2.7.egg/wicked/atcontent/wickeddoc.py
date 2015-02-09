##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Open Planning Project (http://www.openplans.org/)
#   - Rob Miller <rob@kalistra.com> (RaFromBRC)
#   - and contributors
#
##########################################################
"""
WickedDoc
~~~~~~~~~~

A simple subclass of the ATDocument type that supports wicked
linking in the primary text field.

"""
from AccessControl import ClassSecurityInfo
from Products.Archetypes import public as atapi
from Products.CMFCore import permissions as CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from wicked.at.field import WikiField
from wicked.atcontent import zope2
from wicked.interfaces import IAmWicked
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.interface import implements

try:
    from Products.ATContentTypes.atct import ATDocument
except ImportError: # ATCT 0.2
    from Products.ATContentTypes.types.ATDocument import ATDocument
try:
    from Products.ATContentTypes.config import zconf
    ATDOCUMENT_CONTENT_TYPE = zconf.ATDocument.default_content_type
except ImportError: # ATCT 0.2
    from Products.ATContentTypes.config import ATDOCUMENT_CONTENT_TYPE


class WickedDoc(ATDocument):
    """ A page in the portal; supports wiki linking. """
    implements(IAmWicked, IAttributeAnnotatable)
    archetype_name='Wicked Doc'
    portal_type= meta_type ='WickedDoc'
    global_allow=True
    schema = ATDocument.schema.copy() + atapi.Schema((
        WikiField('text',
                  required=True,
                  searchable=True,
                  primary=True,
                  filters=('Wicked Filter',),
                  validators = ('isTidyHtmlWithCleanup',),
                  default_content_type = ATDOCUMENT_CONTENT_TYPE,
                  default_output_type = 'text/html',
                  allowable_content_types = ('text/structured',
                                             'text/x-rst',
                                             'text/html',
                                             'text/plain',
                                             'text/plain-pre',
                                             'text/python-source',),
                  widget = atapi.RichWidget(description = "The body text "\
                                            "of the document.",
                                            description_msgid = "help_body_text",
                                            label = "Body text",
                                            label_msgid = "label_body_text",
                                            rows = 25,
                                            i18n_domain = "plone")),
        ))

atapi.registerType(WickedDoc, zope2.PROJECTNAME)
