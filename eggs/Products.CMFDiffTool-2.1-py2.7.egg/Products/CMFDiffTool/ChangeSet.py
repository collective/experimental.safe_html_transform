# -*- coding: utf-8 -*-
#
# ChangeSet.py - Zope object representing the differences between
# objects
#
# Code by Brent Hendricks
#
# (C) 2003 Brent Hendricks - licensed under the terms of the
# GNU General Public License (GPL).  See LICENSE.txt for details

import logging
from zope.interface import implements

from AccessControl import ClassSecurityInfo
from Acquisition import Implicit
from Acquisition import aq_base
from ComputedAttribute import ComputedAttribute
from Products.CMFCore.utils import getToolByName
from Products.CMFDiffTool.interfaces import IChangeSet

logger = logging.getLogger('CMFDiffTool')

class BaseChangeSet(Implicit):
    """A ChangeSet represents the set of differences between two objects"""

    implements(IChangeSet)
    # This should really not be needed just for same, we should use a method
    __allow_access_to_unprotected_subobjects__ = 1
    security = ClassSecurityInfo()

    def __init__(self, id, title=''):
        """ChangeSet constructor"""
        self.id = id
        self.title = title
        self._diffs = []
        self._added = []
        self._removed = []
        self.ob1_path = []
        self.ob2_path = []
        self._changesets = {}
        self.recursive = 0

    security.declarePublic('getId')
    def getId(self):
        """ChangeSet id"""
        return self.id

    def __getitem__(self, key):
        return self._changesets[key]

    def _isSame(self):
        """Returns true if there are no differences between the two objects"""
        return reduce(lambda x, y: x and y, [d.same for d in self._diffs], 1)

    security.declarePublic('same')
    same = ComputedAttribute(_isSame)

    security.declarePublic('computeDiff')
    def computeDiff(self, ob1, ob2, recursive=1, exclude=None, id1=None, id2=None):
        """Compute the differences from ob1 to ob2 (ie. ob2 - ob1).

        The results can be accessed through getDiffs()"""

        if exclude is None:
            exclude = []

        # Reset state
        self._diffs = []
        self._added = []
        self._removed = []
        self._changed = []
        self._changesets = {}

        purl = getToolByName(self, 'portal_url', None)
        if purl is not None:
            try:
                self.ob1_path = purl.getRelativeContentPath(ob1)
                self.ob2_path = purl.getRelativeContentPath(ob2)
            except AttributeError:
                # one or both of the objects may not have a path
                return
        diff_tool = getToolByName(self, "portal_diff")
        self._diffs = diff_tool.computeDiff(ob1, ob2, id1=id1, id2=id2)

        if recursive and ob1.isPrincipiaFolderish and \
                                                     ob2.isPrincipiaFolderish:
            self.recursive = 1
            ids1 = set(ob1.objectIds())
            ids2 = set(ob2.objectIds())
            self._changed = ids1.intersection(ids2)
            self._removed = ids1.difference(ids2)
            self._added = ids2.difference(ids1)

            # Ignore any excluded items
            for id in exclude:
                try:
                    self._added.remove(id)
                except ValueError:
                    pass
                try:
                    self._removed.remove(id)
                except ValueError:
                    pass
                try:
                    self._changed.remove(id)
                except ValueError:
                    pass

            # Calculate a ChangeSet for every subobject that has changed
            # XXX this is a little strange as self._changed doesn't appear
            # to list changed objects, but rather objects which have been
            # reordered or renamed.
            for id in self._changed:
                self._addSubSet(id, ob1, ob2, exclude, id1, id2)

    def _addSubSet(self, id, ob1, ob2, exclude, id1, id2):
        cs = BaseChangeSet(id, title='Changes to: %s' % id)
        cs = cs.__of__(self)
        cs.computeDiff(ob1[id], ob2[id], exclude=exclude, id1=id1, id2=id2)
        self._changesets[id] = aq_base(cs)

    security.declarePublic('testChanges')
    def testChanges(self, ob):
        """Test the specified object to determine if the change set will apply without errors"""
        for d in self._diffs:
            d.testChanges(ob)

        for id in self._changed:
            cs = self[id]
            child = ob[id]
            cs.testChanges(child)

    security.declarePublic('applyChanges')
    def applyChanges(self, ob):
        """Apply the change set to the specified object"""
        for d in self._diffs:
            d.applyChanges(ob)

        if self._removed:
            ob.manage_delObjects(self._removed)

        for id in self._added:
            child = self[id]
            ob.manage_clone(child, id)

        for id in self._changed:
            cs = self[id]
            child = ob[id]
            cs.applyChanges(child)

    security.declarePublic('getDiffs')
    def getDiffs(self):
        """Returns the list differences between the two objects.

        Each difference is a single object implementing the IDifference interface"""
        return self._diffs

    security.declarePublic('getSubDiffs')
    def getSubDiffs(self):
        """If the ChangeSet was computed recursively, returns a list
           of ChangeSet objects representing subjects differences

           Each ChangeSet will have the same ID as the objects whose
           difference it represents.
           """
        return [self[id] for id in self._changed]

    security.declarePublic('getAddedItems')
    def getAddedItems(self):
        """If the ChangeSet was computed recursively, returns the list
        of IDs of items that were added.

        A copy of these items is available as a cubject of the ChangeSet
        """
        return list(self._added)

    security.declarePublic('getRemovedItems')
    def getRemovedItems(self):
        """If the ChangeSet was computed recursively, returns the list
        of IDs of items that were removed"""
        return list(self._removed)
