from zope.interface import implements

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Acquisition import aq_parent
from Acquisition import aq_inner

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import AddPortalContent
from Products.CMFCore.PortalFolder import PortalFolderBase as PortalFolder

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import LinesField
from Products.Archetypes.atapi import IntegerField
from Products.Archetypes.atapi import MultiSelectionWidget
from Products.Archetypes.atapi import SelectionWidget
from Products.Archetypes.atapi import IntDisplayList
from Products.Archetypes.atapi import DisplayList

from Products.ATContentTypes import ATCTMessageFactory as _
from Products.ATContentTypes import permission as ATCTPermissions

from Products.ATContentTypes.interfaces import ISelectableConstrainTypes

# constants for enableConstrainMixin
ACQUIRE = -1  # acquire locallyAllowedTypes from parent (default)
DISABLED = 0  # use default behavior of PortalFolder which uses the FTI information
ENABLED = 1  # allow types from locallyAllowedTypes only

# Note: ACQUIRED means get allowable types from parent (regardless of
#  whether it supports IConstrainTypes) but only if parent is the same
#  portal_type (folder within folder). Otherwise, use the global_allow/default
#  behaviour (same as DISABLED).

enableDisplayList = IntDisplayList((
    (ACQUIRE, _(u'constraintypes_acquire_label', default=u'Use parent folder settings')),
    (DISABLED, _(u'constraintypes_disable_label', default=u'Use portal default')),
    (ENABLED, _(u'constraintypes_enable_label', default=u'Select manually')),
    ))

ConstrainTypesMixinSchema = Schema((
    IntegerField('constrainTypesMode',
        required=False,
        default_method="_ct_defaultConstrainTypesMode",
        vocabulary=enableDisplayList,
        languageIndependent=True,
        write_permission=ATCTPermissions.ModifyConstrainTypes,
        widget=SelectionWidget(
            label=_(u'label_contrain_types_mode',
                    default=u'Constrain types mode'),
            description=_(u'description_constrain_types_mode',
                          default=u'Select the constraint type mode for this folder.'),
            visible={'view': 'invisible',
                     'edit': 'invisible',
                    },
            ),
        ),

    LinesField('locallyAllowedTypes',
        vocabulary='_ct_vocabularyPossibleTypes',
        enforceVocabulary=False,
        languageIndependent=True,
        default_method='_ct_defaultAddableTypeIds',
        accessor='getLocallyAllowedTypes',  # Respects ENABLE/DISABLE/ACQUIRE
        write_permission=ATCTPermissions.ModifyConstrainTypes,
        multiValued=True,
        widget=MultiSelectionWidget(
            size=10,
            label=_(u'label_constrain_allowed_types',
                    default=u'Permitted types'),
            description=_(u'description_constrain_allowed_types',
                          default=u'Select the types which will be addable inside this folder.'
                         ),
            visible={'view': 'invisible',
                     'edit': 'invisible',
                    },
            ),
        ),

     LinesField('immediatelyAddableTypes',
        vocabulary='_ct_vocabularyPossibleTypes',
        enforceVocabulary=False,
        languageIndependent=True,
        default_method='_ct_defaultAddableTypeIds',
        accessor='getImmediatelyAddableTypes',  # Respects ENABLE/DISABLE/ACQUIRE
        write_permission=ATCTPermissions.ModifyConstrainTypes,
        multiValued=True,
        widget=MultiSelectionWidget(
            size=10,
            label=_(u'label_constrain_preferred_types', u'Preferred types'),
            description=_(u'description_constrain_preferred_types',
                          default=u'Select the types which will be addable '
                                   'from the "Add new item" menu. Any '
                                   'additional types set in the list above '
                                   'will be addable from a separate form.'),
            visible={'view': 'invisible',
                     'edit': 'invisible',
                    },
            ),
        ),
    ))


def getParent(obj):
    portal_factory = getToolByName(obj, 'portal_factory', None)
    if portal_factory is not None and portal_factory.isTemporary(obj):
        # created by portal_factory
        parent = aq_parent(aq_parent(aq_parent(aq_inner(obj))))
    else:
        parent = aq_parent(aq_inner(obj))

    return parent


def parentPortalTypeEqual(obj):
    """Compares the portal type of obj to the portal type of its parent

    Return values:
        None - no acquisition context / parent available
        False - unequal
        True - equal
    """
    parent = getParent(obj)
    if parent is None:
        return None  # no context
    parent_type = getattr(parent.aq_explicit, 'portal_type', None)
    obj_type = getattr(obj.aq_explicit, 'portal_type')
    if obj_type and parent_type == obj_type:
        return True
    return False


class ConstrainTypesMixin:
    """ Gives the user with given rights the possibility to
        constrain the addable types on a per-folder basis.
    """

    implements(ISelectableConstrainTypes)

    security = ClassSecurityInfo()

    #
    # Sanity validator
    #
    security.declareProtected(ModifyPortalContent, 'validate_preferredTypes')
    def validate_preferredTypes(self, value):
        """Ensure that the preferred types is a subset of the allowed types.
        """
        allowed = self.getField('locallyAllowedTypes').get(self)
        preferred = value.split('\n')

        disallowed = []
        for p in preferred:
            if not p in allowed:
                disallowed.append(p)

        if disallowed:
            return "The following types are not permitted: %s" % \
                        ','.join(disallowed)

    #
    # Overrides + supplements for CMF types machinery
    #

    security.declareProtected(View, 'getLocallyAllowedTypes')
    def getLocallyAllowedTypes(self, context=None):
        """If enableTypeRestrictions is ENABLE, return the list of types
        set. If it is ACQUIRE, get the types set on the parent so long
        as the parent is of the same type - if not, use the same behaviuor as
        DISABLE: return the types allowable in the item.
        """
        if context is None:
            context = self
        mode = self.getConstrainTypesMode()

        if mode == DISABLED:
            return [fti.getId() for fti in self.getDefaultAddableTypes(context)]
        elif mode == ENABLED:
            return self.getField('locallyAllowedTypes').get(self)
        elif mode == ACQUIRE:
            parent = getParent(self)
            if not parent or parent.portal_type == 'Plone Site':
                return [fti.getId() for fti in self.getDefaultAddableTypes(context)]
            elif not parentPortalTypeEqual(self):
                # if parent.portal_type != self.portal_type:
                default_addable_types = [fti.getId() for fti in self.getDefaultAddableTypes(context)]
                if ISelectableConstrainTypes.providedBy(parent):
                    return [t for t in parent.getLocallyAllowedTypes(context)
                                if t in default_addable_types]
                else:
                    return [t for t in parent.getLocallyAllowedTypes()
                                if t in default_addable_types]
            else:
                if ISelectableConstrainTypes.providedBy(parent):
                    return parent.getLocallyAllowedTypes(context)
                else:
                    return parent.getLocallyAllowedTypes()
        else:
            raise ValueError, "Invalid value for enableAddRestriction"

    security.declareProtected(View, 'getImmediatelyAddableTypes')
    def getImmediatelyAddableTypes(self, context=None):
        """Get the list of type ids which should be immediately addable.
        If enableTypeRestrictions is ENABLE, return the list set; if it is
        ACQUIRE, use the value from the parent; if it is DISABLE, return
        all type ids allowable on the item.
        """
        if context is None:
            context = self
        mode = self.getConstrainTypesMode()

        if mode == DISABLED:
            return [fti.getId() for fti in \
                        self.getDefaultAddableTypes(context)]
        elif mode == ENABLED:
            return self.getField('immediatelyAddableTypes').get(self)
        elif mode == ACQUIRE:
            parent = getParent(self)
            if not parent or parent.portal_type == 'Plone Site':
                return [fti.getId() for fti in \
                        PortalFolder.allowedContentTypes(self)]
            elif not parentPortalTypeEqual(self):
                default_allowed = [fti.getId() for fti in \
                        PortalFolder.allowedContentTypes(self)]
                return [t for t in parent.getImmediatelyAddableTypes(context) \
                           if t in default_allowed]
            else:
                parent = aq_parent(aq_inner(self))
                return parent.getImmediatelyAddableTypes(context)
        else:
            raise ValueError, "Invalid value for enableAddRestriction"

    # overrides CMFCore's PortalFolder allowedTypes
    def allowedContentTypes(self, context=None):
        """returns constrained allowed types as list of fti's
        """
        if context is None:
            context = self
        mode = self.getConstrainTypesMode()

        # Short circuit if we are disabled or acquiring from non-compatible
        # parent

        parent = getParent(self)
        if mode == DISABLED or (mode == ACQUIRE and not parent):
            return PortalFolder.allowedContentTypes(self)
        elif mode == ACQUIRE and not parentPortalTypeEqual(self):
            globalTypes = self.getDefaultAddableTypes(context)
            if parent.portal_type == 'Plone Site':
                return globalTypes
            else:
                allowed = list(parent.getLocallyAllowedTypes(context))
                return [fti for fti in globalTypes if fti.getId() in allowed]
        else:
            globalTypes = self.getDefaultAddableTypes(context)
            allowed = list(self.getLocallyAllowedTypes())
            ftis = [fti for fti in globalTypes if fti.getId() in allowed]
            return ftis

    # overrides CMFCore's PortalFolder invokeFactory
    security.declareProtected(AddPortalContent, 'invokeFactory')
    def invokeFactory(self, type_name, id, RESPONSE=None, *args, **kw):
        """Invokes the portal_types tool
        """
        mode = self.getConstrainTypesMode()

        # Short circuit if we are disabled or acquiring from non-compatible
        # parent

        #if mode == DISABLED or \
        #        (parent and parent.portal_types != self.portal_types):
        if mode == DISABLED or \
              (mode == ACQUIRE and not parentPortalTypeEqual(self)):
            return PortalFolder.invokeFactory(self, type_name, id,
                                                RESPONSE=None, *args, **kw)

        if not type_name in [fti.getId() for fti in self.allowedContentTypes()]:
            raise ValueError('Disallowed subobject type: %s' % type_name)

        pt = getToolByName(self, 'portal_types')
        args = (type_name, self, id, RESPONSE) + args
        return pt.constructContent(*args, **kw)

    security.declareProtected(View, 'getDefaultAddableTypes')
    def getDefaultAddableTypes(self, context=None):
        """returns a list of normally allowed objects as ftis.
        Exactly like PortalFolder.allowedContentTypes except this
        will check in a specific context.
        """
        if context is None:
            context = self

        portal_types = getToolByName(self, 'portal_types')
        myType = portal_types.getTypeInfo(self)
        result = portal_types.listTypeInfo()
        # Don't give parameter context to portal_types.listTypeInfo().
        # If we do that, listTypeInfo will execute
        # t.isConstructionAllowed(context) for each content type
        # in portal_types.
        # The isConstructionAllowed should be done only on allowed types.
        if myType is not None:
            return [t for t in result if myType.allowType(t.getId()) and
                    t.isConstructionAllowed(context)]

        return [t for t in result if t.isConstructionAllowed(context)]

    security.declarePublic('canSetConstrainTypes')
    def canSetConstrainTypes(self):
        """Find out if the current user is allowed to set the allowable types
        """
        mtool = getToolByName(self, 'portal_membership')
        member = mtool.getAuthenticatedMember()
        return member.has_permission(ATCTPermissions.ModifyConstrainTypes, self)

    #
    # Helper methods
    #

    # Vocab for type lists
    security.declarePrivate('_ct_vocabularyPossibleTypes')
    def _ct_vocabularyPossibleTypes(self):
        """Get a DisplayList of types which may be added (id -> title)
        """
        typelist = [(fti.title_or_id(), fti.getId())
                     for fti in self.getDefaultAddableTypes()]
        typelist.sort()
        return DisplayList([(id, title) for title, id in typelist])

    # Default method for type lists
    security.declarePrivate('_ct_defaultAddableTypeIds')
    def _ct_defaultAddableTypeIds(self):
        """Get a list of types which are addable in the ordinary case w/o the
        constraint machinery.
        """
        return [fti.getId() for fti in self.getDefaultAddableTypes()]

    def _ct_defaultConstrainTypesMode(self):
        """Configure constrainTypeMode depending on the parent

        ACQUIRE if parent support ISelectableConstrainTypes
        DISABLE if not
        """
        portal_factory = getToolByName(self, 'portal_factory', None)
        if portal_factory is not None and portal_factory.isTemporary(self):
            # created by portal_factory
            parent = aq_parent(aq_parent(aq_parent(aq_inner(self))))
        else:
            parent = aq_parent(aq_inner(self))

        if ISelectableConstrainTypes.providedBy(parent) and parentPortalTypeEqual(self):
            return ACQUIRE
        else:
            return DISABLED

InitializeClass(ConstrainTypesMixin)
