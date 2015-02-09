from zope.interface import implements

from Products.CMFCore.permissions import View
from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import BooleanField
from Products.Archetypes.atapi import BooleanWidget
from Products.Archetypes.atapi import ReferenceField
from Products.Archetypes.Referenceable import Referenceable

from Products.ATContentTypes.criteria import registerCriterion
from Products.ATContentTypes.criteria import PATH_INDICES
from Products.ATContentTypes.criteria.base import ATBaseCriterion
from Products.ATContentTypes.criteria.schemata import ATBaseCriterionSchema
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion
from Products.ATContentTypes.permission import ChangeTopics

from archetypes.referencebrowserwidget import ReferenceBrowserWidget

from Products.ATContentTypes import ATCTMessageFactory as _

ATPathCriterionSchema = ATBaseCriterionSchema + Schema((
    ReferenceField('value',
                required=1,
                mode="rw",
                write_permission=ChangeTopics,
                accessor="Value",
                mutator="setValue",
                allowed_types_method="getNavTypes",
                multiValued=True,
                keepReferencesOnCopy=True,
                relationship="paths",
                widget=ReferenceBrowserWidget(
                    allow_search=1,
                    label=_(u'label_path_criteria_value', default=u'Folders'),
                    description=_(u'help_path_criteria_value',
                                  default=u'Folders to search in.'),
                    base_query={'is_folderish': True},
                    restrict_browse=True,
                    startup_directory='../')
                ),
    BooleanField('recurse',
                mode="rw",
                write_permission=ChangeTopics,
                accessor="Recurse",
                default=False,
                widget=BooleanWidget(
                    label=_(u'label_path_criteria_recurse', default=u'Search Sub-Folders'),
                    description='',
                    ),
                ),
    ))


class ATPathCriterion(ATBaseCriterion):
    """A path criterion"""

    implements(IATTopicSearchCriterion)

    security = ClassSecurityInfo()
    schema = ATPathCriterionSchema
    meta_type = 'ATPathCriterion'
    archetype_name = 'Path Criterion'
    shortDesc = 'Location in site'

    def getNavTypes(self):
        ptool = self.plone_utils
        nav_types = ptool.typesToList()
        return nav_types

    # Override reference mutator, so that it always reindexes
    def setValue(self, value):
        self.getField('value').set(self, value)
        self.reindexObject()

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems(self):
        result = []
        depth = (not self.Recurse() and 1) or -1
        paths = ['/'.join(o.getPhysicalPath()) for o in self.Value() if o is not None]

        if paths is not '':
            result.append((self.Field(), {'query': paths, 'depth': depth}))

        return tuple(result)

    # We need references, so we need to be partly cataloged
    _catalogUID = Referenceable._catalogUID
    _catalogRefs = Referenceable._catalogRefs
    _unregister = Referenceable._unregister
    _updateCatalog = Referenceable._updateCatalog
    _referenceApply = Referenceable._referenceApply
    _uncatalogUID = Referenceable._uncatalogUID
    _uncatalogRefs = Referenceable._uncatalogRefs

    def reindexObject(self, *args, **kwargs):
        self._catalogUID(self)
        self._catalogRefs(self)

    def unindexObject(self, *args, **kwargs):
        self._uncatalogUID(self)
        self._uncatalogRefs(self)

    def indexObject(self, *args, **kwargs):
        self._catalogUID(self)
        self._catalogRefs(self)

registerCriterion(ATPathCriterion, PATH_INDICES)
