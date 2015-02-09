from Products.Archetypes import public as atapi
from Products.CMFCore.permissions import setDefaultRoles
import Products.Archetypes.public as atapi

PROJECTNAME='wicked.atcontent'

import migration

def initialize(context):
    """load up content types"""
    from Products.CMFCore import utils as cmf_utils
    #app = context._ProductContext__app
    #patch_listDefaultTypeInformation(app)

    from ironicwiki import IronicWiki
    try:
        from wickeddoc import WickedDoc
    except ImportError: # no ATCT
        pass

    types = atapi.listTypes(PROJECTNAME)
    content_types, constructors, ftis = atapi.process_types( types,
                                                             PROJECTNAME)
    permissions = {}
    types = atapi.listTypes(PROJECTNAME)

    for atype in  types:
        permission = "%s: Add %s" % (PROJECTNAME, atype['portal_type'])
        permissions[atype['portal_type']] = permission

        # Assign default roles
        setDefaultRoles(permission, ('Manager', 'Owner'))

    allTypes = zip(content_types, constructors)
    for atype, constructor in allTypes:
        kind = "%s: %s" % (PROJECTNAME, atype.archetype_name)
        cmf_utils.ContentInit(
            kind,
            content_types      = (atype,),
            permission         = permissions[atype.portal_type],
            extra_constructors = (constructor,),
            fti                = ftis,
            ).initialize(context)
