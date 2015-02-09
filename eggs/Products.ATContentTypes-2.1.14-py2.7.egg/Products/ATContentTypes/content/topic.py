from types import ListType
from types import TupleType
from types import StringType

from zope.interface import implements

from ZPublisher.HTTPRequest import HTTPRequest
from Products.ZCatalog.Lazy import LazyCat
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import AddPortalContent
from Products.CMFCore.utils import getToolByName
from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from Acquisition import aq_parent
from Acquisition import aq_inner
from webdav.Resource import Resource as WebdavResoure

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import TextField
from Products.Archetypes.atapi import BooleanField
from Products.Archetypes.atapi import IntegerField
from Products.Archetypes.atapi import LinesField
from Products.Archetypes.atapi import BooleanWidget
from Products.Archetypes.atapi import IntegerWidget
from Products.Archetypes.atapi import InAndOutWidget
from Products.Archetypes.atapi import RichWidget
from Products.Archetypes.atapi import DisplayList
from Products.Archetypes.atapi import AnnotationStorage

from Products.ATContentTypes.configuration import zconf
from Products.ATContentTypes.config import PROJECTNAME
from Products.ATContentTypes.content.base import registerATCT
from Products.ATContentTypes.content.base import ATCTFolder
from Products.ATContentTypes.criteria import _criterionRegistry
from Products.ATContentTypes.exportimport.content import IDisabledExport
from Products.ATContentTypes.content.schemata import ATContentTypeSchema
from Products.ATContentTypes.content.schemata import finalizeATCTSchema
from Products.ATContentTypes.interfaces import IATTopic
from Products.ATContentTypes.interfaces import IATTopicSearchCriterion
from Products.ATContentTypes.interfaces import IATTopicSortCriterion
from Products.ATContentTypes.permission import ChangeTopics

from Products.ATContentTypes.config import TOOLNAME

from Products.ATContentTypes import ATCTMessageFactory as _
from Products.CMFPlone.PloneBatch import Batch

# A couple of fields just don't make sense to sort (for a user),
# some are just doubles.
IGNORED_FIELDS = ['Date', 'allowedRolesAndUsers', 'getId', 'in_reply_to',
    'meta_type',
    # 'portal_type' # portal type and Type might differ!
    ]

ATTopicSchema = ATContentTypeSchema.copy() + Schema((
    TextField('text',
              required=False,
              searchable=True,
              primary=True,
              storage=AnnotationStorage(migrate=True),
              validators=('isTidyHtmlWithCleanup',),
              #validators=('isTidyHtml',),
              default_output_type='text/x-html-safe',
              write_permission=ChangeTopics,
              widget=RichWidget(
                    description='',
                    label=_(u'label_body_text', default=u'Body Text'),
                    rows=25,
                    allow_file_upload=zconf.ATDocument.allow_document_upload),
    ),
    BooleanField('acquireCriteria',
                required=False,
                mode="rw",
                default=False,
                write_permission=ChangeTopics,
                widget=BooleanWidget(
                        label=_(u'label_inherit_criteria', default=u'Inherit Criteria'),
                        description=_(u'help_inherit_collection_criteria',
                                      default=u"Narrow down the search results from the parent Collection(s) "
                                               "by using the criteria from this Collection."),
                        # Only show when the parent object is a Topic also,
                        condition="python:object.aq_parent.portal_type == 'Topic'"),
                ),
    BooleanField('limitNumber',
                required=False,
                mode="rw",
                default=False,
                write_permission=ChangeTopics,
                widget=BooleanWidget(
                        label=_(u'label_limit_number', default=u'Limit Search Results'),
                        description=_(u'help_limit_number',
                                      default=u"If selected, only the 'Number of Items' "
                                               "indicated below will be displayed.")
                        ),
                ),
    IntegerField('itemCount',
                required=False,
                mode="rw",
                default=0,
                write_permission=ChangeTopics,
                widget=IntegerWidget(
                        label=_(u'label_item_count', default=u'Number of Items'),
                        description=''
                        ),
                 ),
    BooleanField('customView',
                required=False,
                mode="rw",
                default=False,
                write_permission=ChangeTopics,
                widget=BooleanWidget(
                        label=_(u'label_custom_view', default=u'Display as Table'),
                        description=_(u'help_custom_view',
                                      default=u"Columns in the table are controlled "
                                               "by 'Table Columns' below.")
                        ),
                 ),
    LinesField('customViewFields',
                required=False,
                mode="rw",
                default=('Title',),
                vocabulary='listMetaDataFields',
                enforceVocabulary=True,
                write_permission=ChangeTopics,
                widget=InAndOutWidget(
                        label=_(u'label_custom_view_fields', default=u'Table Columns'),
                        description=_(u'help_custom_view_fields',
                                      default=u"Select which fields to display when "
                                               "'Display as Table' is checked.")
                        ),
                 ),
    ))
finalizeATCTSchema(ATTopicSchema, folderish=False, moveDiscussion=False)


class ATTopic(ATCTFolder):
    """An automatically updated stored search that can be used to display items matching criteria you specify."""

    schema = ATTopicSchema

    portal_type = 'Topic'
    archetype_name = 'Collection'
    _atct_newTypeFor = {'portal_type': 'CMF Topic', 'meta_type': 'Portal Topic'}
    assocMimetypes = ()
    assocFileExt = ()
    cmf_edit_kws = ()

    use_folder_tabs = 0

    implements(IATTopic, IDisabledExport)

    # Enable marshalling via WebDAV/FTP
    __dav_marshall__ = True

    security = ClassSecurityInfo()

    # Override initializeArchetype to turn on syndication by default
    def initializeArchetype(self, **kwargs):
        ret_val = ATCTFolder.initializeArchetype(self, **kwargs)
        # Enable topic syndication by default
        syn_tool = getToolByName(self, 'portal_syndication', None)
        if syn_tool is not None:
            if (syn_tool.isSiteSyndicationAllowed() and
                                    not syn_tool.isSyndicationAllowed(self)):
                syn_tool.enableSyndication(self)
        return ret_val

    security.declareProtected(ChangeTopics, 'validateAddCriterion')
    def validateAddCriterion(self, indexId, criteriaType):
        """Is criteriaType acceptable criteria for indexId
        """
        return criteriaType in self.criteriaByIndexId(indexId)

    security.declareProtected(ChangeTopics, 'criteriaByIndexId')
    def criteriaByIndexId(self, indexId):
        catalog_tool = getToolByName(self, 'portal_catalog')
        indexObj = catalog_tool.Indexes[indexId]
        results = _criterionRegistry.criteriaByIndex(indexObj.meta_type)
        return results

    security.declareProtected(ChangeTopics, 'listCriteriaTypes')
    def listCriteriaTypes(self):
        """List available criteria types as dict
        """
        return [{'name': ctype,
                 'description':_criterionRegistry[ctype].shortDesc}
                for ctype in self.listCriteriaMetaTypes()]

    security.declareProtected(ChangeTopics, 'listCriteriaMetaTypes')
    def listCriteriaMetaTypes(self):
        """List available criteria
        """
        val = _criterionRegistry.listTypes()
        val.sort()
        return val

    security.declareProtected(ChangeTopics, 'listSearchCriteriaTypes')
    def listSearchCriteriaTypes(self):
        """List available search criteria types as dict
        """
        return [{'name': ctype,
                 'description':_criterionRegistry[ctype].shortDesc}
                for ctype in self.listSearchCriteriaMetaTypes()]

    security.declareProtected(ChangeTopics, 'listSearchCriteriaMetaTypes')
    def listSearchCriteriaMetaTypes(self):
        """List available search criteria
        """
        val = _criterionRegistry.listSearchTypes()
        val.sort()
        return val

    security.declareProtected(ChangeTopics, 'listSortCriteriaTypes')
    def listSortCriteriaTypes(self):
        """List available sort criteria types as dict
        """
        return [{'name': ctype,
                 'description':_criterionRegistry[ctype].shortDesc}
                for ctype in self.listSortCriteriaMetaTypes()]

    security.declareProtected(ChangeTopics, 'listSortCriteriaMetaTypes')
    def listSortCriteriaMetaTypes(self):
        """List available sort criteria
        """
        val = _criterionRegistry.listSortTypes()
        val.sort()
        return val

    security.declareProtected(View, 'listCriteria')
    def listCriteria(self):
        """Return a list of our criteria objects.
        """
        val = self.objectValues(self.listCriteriaMetaTypes())
        return val

    security.declareProtected(View, 'listSearchCriteria')
    def listSearchCriteria(self):
        """Return a list of our search criteria objects.
        """
        return [val for val in self.listCriteria() if
             IATTopicSearchCriterion.providedBy(val)]

    security.declareProtected(ChangeTopics, 'hasSortCriterion')
    def hasSortCriterion(self):
        """Tells if a sort criterai is already setup.
        """
        return not self.getSortCriterion() is None

    security.declareProtected(ChangeTopics, 'getSortCriterion')
    def getSortCriterion(self):
        """Return the Sort criterion if setup.
        """
        for criterion in self.listCriteria():
            if IATTopicSortCriterion.providedBy(criterion):
                return criterion
        return None

    security.declareProtected(ChangeTopics, 'removeSortCriterion')
    def removeSortCriterion(self):
        """remove the Sort criterion.
        """
        if self.hasSortCriterion():
            self.deleteCriterion(self.getSortCriterion().getId())

    security.declareProtected(ChangeTopics, 'setSortCriterion')
    def setSortCriterion(self, field, reversed):
        """Set the Sort criterion.
        """
        self.removeSortCriterion()
        self.addCriterion(field, 'ATSortCriterion')
        self.getSortCriterion().setReversed(reversed)

    security.declareProtected(ChangeTopics, 'listIndicesByCriterion')
    def listIndicesByCriterion(self, criterion):
        """
        """
        return _criterionRegistry.indicesByCriterion(criterion)

    security.declareProtected(ChangeTopics, 'listFields')
    def listFields(self):
        """Return a list of fields from portal_catalog.
        """
        tool = getToolByName(self, TOOLNAME)
        return tool.getEnabledFields()

    security.declareProtected(ChangeTopics, 'listSortFields')
    def listSortFields(self):
        """Return a list of available fields for sorting."""
        fields = [field
                    for field in self.listFields()
                    if self.validateAddCriterion(field[0], 'ATSortCriterion')]
        return fields

    security.declareProtected(ChangeTopics, 'listAvailableFields')
    def listAvailableFields(self):
        """Return a list of available fields for new criteria.
        """
        current = [crit.Field() for crit in self.listCriteria()
                      if not IATTopicSortCriterion.providedBy(crit)]
        fields = self.listFields()
        val = [field
                 for field in fields
                 if field[0] not in current
              ]
        return val

    security.declareProtected(View, 'listSubtopics')
    def listSubtopics(self):
        """Return a list of our subtopics.
        """
        val = self.objectValues(self.meta_type)
        check_p = getToolByName(self, 'portal_membership').checkPermission
        tops = []
        for top in val:
            if check_p('View', top):
                tops.append((top.Title().lower(), top))
        tops.sort()
        tops = [t[1] for t in tops]
        return tops

    security.declareProtected(View, 'hasSubtopics')
    def hasSubtopics(self):
        """Returns true if subtopics have been created on this topic.
        """
        val = self.objectIds(self.meta_type)
        return not not val

    security.declareProtected(View, 'listMetaDataFields')
    def listMetaDataFields(self, exclude=True):
        """Return a list of metadata fields from portal_catalog.
        """
        tool = getToolByName(self, TOOLNAME)
        return tool.getMetadataDisplay(exclude)

    security.declareProtected(View, 'allowedCriteriaForField')
    def allowedCriteriaForField(self, field, display_list=False):
        """ Return all valid criteria for a given field.  Optionally include
            descriptions in list in format [(desc1, val1) , (desc2, val2)] for
            javascript selector."""
        tool = getToolByName(self, TOOLNAME)
        criteria = tool.getIndex(field).criteria
        allowed = [crit for crit in criteria
                                if self.validateAddCriterion(field, crit)]
        if display_list:
            flat = []
            for a in allowed:
                desc = _criterionRegistry[a].shortDesc
                flat.append((a, desc))
            allowed = DisplayList(flat)
        return allowed

    security.declareProtected(View, 'buildQuery')
    def buildQuery(self):
        """Construct a catalog query using our criterion objects.
        """
        result = {}
        clear_start = False
        criteria = self.listCriteria()
        acquire = self.getAcquireCriteria()
        if not criteria and not acquire:
            # no criteria found
            return None

        if acquire:
            try:
                # Tracker 290 asks to allow combinations, like this:
                # parent = aq_parent(self)
                clear_start = True
                parent = aq_parent(aq_inner(self))
                result.update(parent.buildQuery())
            except (AttributeError, Unauthorized):  # oh well, can't find parent, or it isn't a Topic.
                pass

        for criterion in criteria:
            for key, value in criterion.getCriteriaItems():
                # Ticket: https://dev.plone.org/plone/ticket/8827
                # If a sub topic is set to acquire then the 'start' key have to
                # be deleted to get ATFriendlyDateCriteria to work properly (the 'end' key) -
                # so the 'start' key should be deleted.
                # But only when:
                # - a subtopic with acquire enabled
                # - its a ATFriendlyDateCriteria
                # - the date criteria is set to 'now' (0)
                # - the end key is set
                if clear_start and criterion.meta_type in ['ATFriendlyDateCriteria'] \
                and not criterion.value and key == 'end' and 'start' in result:
                    del result['start']
                result[key] = value
        return result

    security.declareProtected(View, 'queryCatalog')
    def queryCatalog(self, REQUEST=None, batch=False, b_size=None,
                                                    full_objects=False, **kw):
        # Invoke the catalog using our criteria to augment any passed
        # in query before calling the catalog.
        if REQUEST is None:
            REQUEST = getattr(self, 'REQUEST', {})
        b_start = REQUEST.get('b_start', 0)

        pcatalog = getToolByName(self, 'portal_catalog')
        mt = getToolByName(self, 'portal_membership')
        related = [i for i in self.getRelatedItems() \
                        if mt.checkPermission(View, i)]
        if not full_objects:
            uids = [r.UID() for r in related]
            query = dict(UID=uids)
            related = pcatalog(query)
        related = LazyCat([related])

        limit = self.getLimitNumber()
        max_items = self.getItemCount()
        # Batch based on limit size if b_size is unspecified
        if max_items and b_size is None:
            b_size = int(max_items)
        else:
            b_size = b_size or 20

        q = self.buildQuery()
        if q is None:
            results = LazyCat([[]])
        else:
            # Allow parameters to further limit existing criterias
            q.update(kw)
            if not batch and limit and max_items and self.hasSortCriterion():
                q.setdefault('sort_limit', max_items)
            if batch:
                q['b_start'] = b_start
                q['b_size'] = b_size
            __traceback_info__ = (self, q)
            results = pcatalog.searchResults(q)

        if limit and not batch:
            if full_objects:
                return related[:max_items] + \
                       [b.getObject() for b in results[:max_items - len(related)]]
            return related[:max_items] + results[:max_items - len(related)]
        elif full_objects:
            results = related + LazyCat([[b.getObject() for b in results]])
        else:
            results = related + results
        if batch:
            batch = Batch(results, b_size, int(b_start), orphan=0)
            return batch
        return results

    security.declareProtected(ChangeTopics, 'addCriterion')
    def addCriterion(self, field, criterion_type):
        """Add a new search criterion. Return the resulting object.
        """
        newid = 'crit__%s_%s' % (field, criterion_type)
        ct = _criterionRegistry[criterion_type]
        crit = ct(newid, field)

        self._setObject(newid, crit)
        return self._getOb(newid)

    security.declareProtected(ChangeTopics, 'deleteCriterion')
    def deleteCriterion(self, criterion_id):
        """Delete selected criterion.
        """
        if type(criterion_id) is StringType:
            self._delObject(criterion_id)
        elif type(criterion_id) in (ListType, TupleType):
            for cid in criterion_id:
                self._delObject(cid)

    security.declareProtected(View, 'getCriterion')
    def getCriterion(self, criterion_id):
        """Get the criterion object.
        """
        try:
            return self._getOb('crit__%s' % criterion_id)
        except AttributeError:
            return self._getOb(criterion_id)

    security.declareProtected(AddPortalContent, 'addSubtopic')
    def addSubtopic(self, id):
        """Add a new subtopic.
        """
        ti = self.getTypeInfo()
        ti.constructInstance(self, id)
        return self._getOb(id)

    security.declareProtected(View, 'synContentValues')
    def synContentValues(self):
        """Getter for syndacation support
        """
        syn_tool = getToolByName(self, 'portal_syndication')
        limit = int(syn_tool.getMaxItems(self))
        return self.queryCatalog(sort_limit=limit)[:limit]

    security.declarePublic('canSetDefaultPage')
    def canSetDefaultPage(self):
        """
        Override BrowserDefaultMixin because default page stuff doesn't make
        sense for topics.
        """
        return False

    security.declarePublic('getCriterionUniqueWidgetAttr')
    def getCriteriaUniqueWidgetAttr(self, attr):
        """Get a unique list values for a specific attribute for all widgets
           on all criteria"""
        criteria = self.listCriteria()
        order = []
        for crit in criteria:
            fields = crit.Schema().fields()
            for f in fields:
                widget = f.widget
                helper = getattr(widget, attr, None)
                # We expect the attribute value to be a iterable.
                if helper:
                    [order.append(item) for item in helper
                        if item not in order]
        return order

    security.declareProtected(View, 'HEAD')
    def HEAD(self, REQUEST, RESPONSE):
        """HTTP HEAD handler"""
        return WebdavResoure.HEAD(self, REQUEST, RESPONSE)

    security.declareProtected(ChangeTopics, 'setText')
    def setText(self, value, **kwargs):
        """Body text mutator

        * hook into mxTidy an replace the value with the tidied value
        """
        field = self.getField('text')

        # When an object is initialized the first time we have to
        # set the filename and mimetype.
        if not value and not field.getRaw(self):
            if 'mimetype' in kwargs and kwargs['mimetype']:
                field.setContentType(self, kwargs['mimetype'])
            if 'filename' in kwargs and kwargs['filename']:
                field.setFilename(self, kwargs['filename'])

        # hook for mxTidy / isTidyHtmlWithCleanup validator
        tidyOutput = self.getTidyOutput(field)
        if tidyOutput:
            value = tidyOutput

        field.set(self, value, **kwargs)  # set is ok

    security.declarePrivate('getTidyOutput')
    def getTidyOutput(self, field):
        """Get the tidied output for a specific field from the request
        if available
        """
        request = getattr(self, 'REQUEST', None)
        if request is not None and isinstance(request, HTTPRequest):
            tidyAttribute = '%s_tidier_data' % field.getName()
            return request.get(tidyAttribute, None)

registerATCT(ATTopic, PROJECTNAME)
