import os.path
import sys
import logging

logger = logging.getLogger('ATCT')

ATCT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(3, os.path.join(ATCT_DIR, 'thirdparty'))

from AccessControl import ModuleSecurityInfo

from Products.ATContentTypes.config import HAS_LINGUA_PLONE
from Products.ATContentTypes.config import SKINS_DIR
from Products.ATContentTypes.config import PROJECTNAME
from Products.ATContentTypes.config import GLOBALS

from Products.CMFCore.utils import ContentInit
from Products.CMFCore.utils import ToolInit
from Products.CMFCore.DirectoryView import registerDirectory

# Import "ATCTMessageFactory as _" to create messages in atcontenttypes domain
from zope.i18nmessageid import MessageFactory
ATCTMessageFactory = MessageFactory('atcontenttypes')
ModuleSecurityInfo('Products.ATContentTypes').declarePublic('ATCTMessageFactory')

# first level imports: configuration and validation
import Products.ATContentTypes.configuration
import Products.ATContentTypes.lib.validators

# second leven imports: content types, criteria
# the content types are depending on the validators and configuration
import Products.ATContentTypes.content
import Products.ATContentTypes.criteria

# misc imports
from Products.ATContentTypes.tool.atct import ATCTTool

# wire the add permission after all types are registered
from Products.ATContentTypes.permission import wireAddPermissions
wireAddPermissions()

registerDirectory(SKINS_DIR, GLOBALS)


def initialize(context):
    # process our custom types
    if HAS_LINGUA_PLONE:
        from Products.LinguaPlone.public import process_types
        from Products.LinguaPlone.public import listTypes
    else:
        from Products.Archetypes.atapi import process_types
        from Products.Archetypes.atapi import listTypes

    ToolInit(
        'ATContentTypes tool',
        tools=(ATCTTool,),
        icon='tool.gif', ).initialize(context)

    listOfTypes = listTypes(PROJECTNAME)

    content_types, constructors, ftis = process_types(
        listOfTypes,
        PROJECTNAME)

    # Assign an own permission to all content types
    # Heavily based on Bricolite's code from Ben Saller
    from Products.ATContentTypes.permission import permissions

    allTypes = zip(content_types, constructors)
    for atype, constructor in allTypes:
        kind = "%s: %s" % (PROJECTNAME, atype.archetype_name)
        ContentInit(
            kind,
            content_types=(atype,),
            permission=permissions[atype.portal_type],
            extra_constructors=(constructor,),
            ).initialize(context)
