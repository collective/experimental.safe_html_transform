from UserDict import UserDict
from Products.Archetypes.atapi import registerType
from Products.Archetypes.ClassGen import generateClass
from Products.ATContentTypes.config import PROJECTNAME
from types import StringType

from Products.ATContentTypes.interfaces import IATTopicCriterion
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion
from Products.ATContentTypes.interfaces import IATTopicSortCriterion

ALL_INDICES = ('DateIndex', 'DateRangeIndex', 'FieldIndex', 'KeywordIndex',
               'PathIndex', 'TextIndex', 'TextIndexNG2', 'TextIndexNG3',
               'TopicIndex', 'ZCTextIndex', 'NavtreeIndexNG',
               'ExtendedPathIndex', 'BooleanIndex', 'UUIDIndex')

SORT_INDICES = ('DateIndex', 'DateRangeIndex', 'FieldIndex', 'KeywordIndex',
                'PathIndex', 'GopipIndex')
# TextIndex, TopicIndex, ZCTextIndex, TextIndexNG2, NavtreeIndexNG
# are not usable to sort as they do not have 'keyForDocument' attribute

DATE_INDICES = ('DateIndex', 'DateRangeIndex', 'FieldIndex')

# Indices that can take a list of values
LIST_INDICES = ('FieldIndex', 'KeywordIndex', 'PathIndex', 'NavtreeIndexNG',
                  'ExtendedPathIndex', 'TopicIndex')

TEXT_INDICES = ('TextIndex', 'TextIndexNG2', 'TextIndexNG3', 'ZCTextIndex')

# Indices that can take a simple string
STRING_INDICES = LIST_INDICES + TEXT_INDICES

# Indices that may hold AT reference data
REFERENCE_INDICES = ('FieldIndex', 'KeywordIndex')
FIELD_INDICES = ('FieldIndex',)
PATH_INDICES = ('PathIndex', 'ExtendedPathIndex')


class _CriterionRegistry(UserDict):
    """Registry for criteria """

    def __init__(self, *args, **kwargs):
        UserDict.__init__(self, *args, **kwargs)
        self.index2criterion = {}
        self.criterion2index = {}
        self.portaltypes = {}

    def register(self, criterion, indices):
        if type(indices) is StringType:
            indices = (indices,)
        indices = tuple(indices)

        if indices == ():
            indices = ALL_INDICES

        assert IATTopicCriterion.implementedBy(criterion)
        registerType(criterion, PROJECTNAME)

        crit_id = criterion.meta_type
        self[crit_id] = criterion
        self.portaltypes[criterion.portal_type] = criterion

        self.criterion2index[crit_id] = indices
        for index in indices:
            value = self.index2criterion.get(index, ())
            self.index2criterion[index] = value + (crit_id,)

    def unregister(self, criterion):
        crit_id = criterion.meta_type
        self.pop(crit_id)
        self.criterion2index.pop(crit_id)
        for (index, value) in self.index2criterion.items():
            if id in value:
                valuelist = list(value)
                del valuelist[valuelist.index(crit_id)]
                self.index2criterion[index] = tuple(valuelist)

    def listTypes(self):
        return self.keys()

    def listSortTypes(self):
        return [key for key in self.keys()
                    if IATTopicSortCriterion.implementedBy(self[key])]

    def listSearchTypes(self):
        return [key for key in self.keys()
                    if IATTopicSearchCriterion.implementedBy(self[key])]

    def listCriteria(self):
        return self.values()

    def indicesByCriterion(self, criterion):
        return self.criterion2index[criterion]

    def criteriaByIndex(self, index):
        try:
            return self.index2criterion[index]
        except KeyError:
            return ()

    def getPortalTypes(self):
        return tuple(self.portaltypes.keys())

_criterionRegistry = _CriterionRegistry()
registerCriterion = _criterionRegistry.register
unregisterCriterion = _criterionRegistry.unregister

__all__ = ('registerCriterion', 'ALL_INDICES', 'DATE_INDICES', 'STRING_INDICES',
           'LIST_INDICES', 'SORT_INDICES', )

# criteria
from Products.ATContentTypes.criteria.boolean import ATBooleanCriterion
from Products.ATContentTypes.criteria.date import ATDateCriteria
from Products.ATContentTypes.criteria.daterange import ATDateRangeCriterion
from Products.ATContentTypes.criteria.list import ATListCriterion
from Products.ATContentTypes.criteria.portaltype import ATPortalTypeCriterion
from Products.ATContentTypes.criteria.reference import ATReferenceCriterion
from Products.ATContentTypes.criteria.selection import ATSelectionCriterion
from Products.ATContentTypes.criteria.simpleint import ATSimpleIntCriterion
from Products.ATContentTypes.criteria.simplestring import ATSimpleStringCriterion
from Products.ATContentTypes.criteria.sort import ATSortCriterion
from Products.ATContentTypes.criteria.currentauthor import ATCurrentAuthorCriterion
from Products.ATContentTypes.criteria.path import ATPathCriterion
from Products.ATContentTypes.criteria.relativepath import ATRelativePathCriterion
