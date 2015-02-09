##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Open Planning Project (http://www.openplans.org/)
#   - Whit Morriss <whit@kalistra.com>
#   - and contributors
#
##########################################################

"""
IronicWiki
~~~~~~~~~~

a demonstration of wicked's capabilities confined to the content type
wicked aspires to make obsolete

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


class IronicWiki(atapi.BaseContent):
    """ Ironic wiki Portal Content """
    implements(IAmWicked, IAttributeAnnotatable)
    archetype_name = portal_type = meta_type = 'IronicWiki'
    schema = atapi.BaseSchema.copy() + atapi.Schema((
        WikiField( "body",
                   primary=True,
                   filters=('Wicked Filter',),
                   default_content_type='text/structured',
                   default_output_type='text/html',
                   allowable_content_types = ('text/structured',
                                              'text/restructured',
                                              'text/html',
                                              'text/plain',
                                              'text/plain-pre'),

                   widget=atapi.RichWidget( description = "The body text of the document.",
                                            description_msgid = "help_body_text",
                                            label = "Body text",
                                            label_msgid = "label_body_text",
                                            rows = 25,
                                            i18n_domain = "plone")),
        ))


atapi.registerType(IronicWiki, zope2.PROJECTNAME)
