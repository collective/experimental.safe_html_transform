# -*- coding: utf-8 -*-
"""CMFDiffTool.py

   Calculate differences between content objects
"""

from zope.interface import implements

from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.SimpleItem import SimpleItem
from zExceptions import BadRequest

from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import UniqueObject
from Products.CMFDiffTool.interfaces import IDiffTool
from Products.CMFDiffTool.ChangeSet import BaseChangeSet
from Products.PageTemplates.PageTemplateFile import PageTemplateFile


class CMFDiffTool(UniqueObject, SimpleItem):
    """ """

    id = 'portal_diff'
    meta_type = 'CMF Diff Tool'

    security = ClassSecurityInfo()

    manage_options=(( {'label':'Configure', 'action':'manage_difftypes'},
                      {'label':'Overview', 'action':'manage_overview'},
                      ) + SimpleItem.manage_options
                    )

    implements(IDiffTool)

    ## Internal attributes
    _difftypes = {}

    def __init__(self):
        self._pt_diffs = {}

    security.declareProtected(ManagePortal, 'manage_difftypes')
    manage_difftypes = PageTemplateFile('zpt/editCMFDiffTool', globals() )


    def manage_editDiffFields(self, updates, REQUEST=None):
        """Edit the portal type fields"""

        # Clear the old values
        del self._pt_diffs
        self._pt_diffs = {}
        for r in updates:
            if r.get('delete', None):
                continue
            self.setDiffField(r.pt_name, r.field, r.diff)

        self._p_changed = 1
        
        if REQUEST:
            return self.manage_difftypes(manage_tabs_message="Diff mappings updated")


    security.declareProtected(ManagePortal, 'listDiffTypes')
    def manage_addDiffField(self, pt_name, field, diff, REQUEST=None):
        """Add a new diff field from the ZMI"""
        self.setDiffField(pt_name, field, diff)
        if REQUEST:
            return self.manage_difftypes(manage_tabs_message="Field added")
        
        
    def setDiffField(self, pt_name, field, diff):
        """Set the diff type for 'field' on the portal type 'pt_name' to 'diff'"""
        if pt_name not in self.portal_types.listContentTypes():
            raise BadRequest("Error: invalid portal type")

        elif not field:
            raise BadRequest("Error: no field specified")

        elif diff not in self.listDiffTypes():
            raise BadRequest("Error: invalid diff type")

        else:
            self._pt_diffs.setdefault(pt_name, {})[field] = diff
            self._p_changed = 1


    ## Interface fulfillment ##
    security.declareProtected(ManagePortal, 'listDiffTypes')
    def listDiffTypes(self):
        """List the names of the registered difference types"""
        return self._difftypes.keys()

    security.declareProtected(ManagePortal, 'getDiffType')
    def getDiffType(self, diff):
        """Return a class corresponding to the specified diff type.
        Instances of the class will implement the IDifference
        interface"""
        return self._difftypes.get(diff, None)

    security.declareProtected(ManagePortal, 'setDiffForPortalType')
    def setDiffForPortalType(self, pt_name, mapping):
        """Set the difference type(self, s) for the specific portal type

        mapping is a dictionary where each key is an attribute or
        method on the given portal type, and the value is the name of
        a difference type."""
        # FIXME: Do some error checking
        self._pt_diffs[pt_name] = mapping.copy()
        self._p_changed = 1

    security.declareProtected(ManagePortal, 'getDiffForPortalType')
    def getDiffForPortalType(self, pt_name):
        """Returns a dictionary where each key is an attribute or
        method on the given portal type, and the value is the name of
        a difference type."""
        # Return a copy so we don't have to worry about the user changing it
        return self._pt_diffs.get(pt_name, {}).copy()

    security.declarePublic('computeDiff')
    def computeDiff(self, ob1, ob2, id1=None, id2=None):
        """Compute the differences between two objects and return the
        results as a list.  Each object in the list will implement the
        IDifference interface"""

        # Try to get the portal type from obj1 first.  If that fails, use obj2
        pt_name = ''
        try:
            pt_name = aq_base(ob1).portal_type
        except AttributeError:
            try:
                pt_name = aq_base(ob2).portal_type
            except AttributeError:
                pass

        diff_map = self._pt_diffs.get(pt_name, {})

        diffs = []
        for field, klass_name in diff_map.items():
            klass = self._difftypes[klass_name]
            f_diff = klass(ob1, ob2, field, id1=id1, id2=id2)
            # handle compound diff types
            if hasattr(f_diff, '__getitem__'):
                diffs.extend(f_diff)
            else:
                diffs.append(f_diff)
        return diffs

    security.declarePublic('createChangeSet')
    def createChangeSet(self, ob1, ob2, id1=None, id2=None):
        """Returns a ChangeSet object that represents the differences
        between ob1 and ob2 (ie. ob2 - ob1) ."""
        # FIXME: Pick a better ID
        cs = BaseChangeSet('Changes').__of__(self)
        cs.computeDiff(ob1, ob2, id1=id1, id2=id2)
        return aq_base(cs)


def registerDiffType(klass):
    """Register a class for computing differences.

    Instances of the class must implement the IDifference
    interface."""

    CMFDiffTool._difftypes[klass.meta_type] = klass

def unregisterDiffType(klass):
    """Register a class for computing differences.

    Instances of the class must implement the IDifference
    interface."""

    del CMFDiffTool._difftypes[klass.meta_type]


InitializeClass(CMFDiffTool)
registerToolInterface('portal_diff', IDiffTool)
