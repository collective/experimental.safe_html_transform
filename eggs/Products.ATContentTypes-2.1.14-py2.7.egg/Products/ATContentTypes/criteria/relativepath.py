from zope.interface import implements

from Products.CMFCore.permissions import View
from AccessControl import ClassSecurityInfo
from Acquisition import aq_parent

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import BooleanField, StringField
from Products.Archetypes.atapi import BooleanWidget, StringWidget

from Products.ATContentTypes.criteria import registerCriterion
from Products.ATContentTypes.criteria import PATH_INDICES
from Products.ATContentTypes.criteria.base import ATBaseCriterion
from Products.ATContentTypes.criteria.schemata import ATBaseCriterionSchema
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion
from Products.ATContentTypes.permission import ChangeTopics


from Products.CMFCore.utils import getToolByName

ATRelativePathCriterionSchema = ATBaseCriterionSchema + Schema((
    StringField('relativePath',
                default='..',
                widget=StringWidget(label='Relative path',
                                    label_msgid="label_relativepath_criteria_customrelativepath",
                                    description_msgid="help_relativepath_criteria_customrelativepath",
                                    i18n_domain="plone",
                                    description="Enter a relative path e.g.: <br /> '..' for the parent folder <br /> '../..' for the parent's parent <br />'../somefolder' for a sibling folder")),
    BooleanField('recurse',
                mode="rw",
                write_permission=ChangeTopics,
                accessor="Recurse",
                default=False,
                widget=BooleanWidget(
                    label="Search Sub-Folders",
                    label_msgid="label_path_criteria_recurse",
                    description="",
                    description_msgid="help_path_criteria_recurse",
                    i18n_domain="plone"),
                ),
    ))


class ATRelativePathCriterion(ATBaseCriterion):
    """A path criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    schema = ATRelativePathCriterionSchema
    meta_type = 'ATRelativePathCriterion'
    archetype_name = 'Relative Path Criterion'
    shortDesc = 'Location in site relative to the current location'

    def getNavTypes(self):
        ptool = self.plone_utils
        nav_types = ptool.typesToList()
        return nav_types

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems(self):
        result = []
        depth = (not self.Recurse() and 1) or -1
        relPath = self.getRelativePath()

        # sanitize a bit: you never know, with all those windoze users out there
        relPath = relPath.replace("\\", "/")

        # get the path to the portal object
        portalPath = list(getToolByName(self, 'portal_url').getPortalObject().getPhysicalPath())

        if relPath[0] == '/':
            # someone didn't enter a relative path.
            # simply use that one, relative to the portal
            path = '/'.join(portalPath) + relPath
        else:
            folders = relPath.split('/')

            # set the path to the collections path
            path = list(aq_parent(self).getPhysicalPath())

            # now construct an aboslute path based on the relative custom path
            # eat away from 'path' whenever we encounter a '..' in the relative path
            # apend all other elements other than ..
            for folder in folders:
                if folder == '..':
                    # chop off one level from path
                    if path == portalPath:
                        # can't chop off more
                        # just return this path and leave the loop
                        break
                    else:
                        path = path[:-1]
                elif folder == '.':
                    # don't really need this but for being complete
                    # strictly speaking some user may use a . aswell
                    pass  # do nothing
                else:
                    path.append(folder)
            path = '/'.join(path)

        if path is not '':
            result.append((self.Field(), {'query': path, 'depth': depth}))

        return tuple(result)


registerCriterion(ATRelativePathCriterion, PATH_INDICES)
