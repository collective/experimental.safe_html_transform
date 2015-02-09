# -*- coding: utf-8 -*-
# Interface definitions
from zope.interface import Interface, Attribute


class IDiffTool(Interface):
    """An interface to compute object differences via pluggable
       difference engine"""

    id = Attribute('id','Must be set to "portal_diff"')


    def listDiffTypes():
        """List the names of the available difference types"""

    def setDiffForPortalType(pt_name, mapping):
        """Set the difference type(s) for the specific portal type

        mapping is a dictionary where each key is an attribute or
        method on the given portal type, and the value is the name of
        a difference type."""

    def getDiffForPortalType(pt_name):
        """Returns a dictionary where each key is an attribute or
        method on the given portal type, and the value is the name of
        a difference type."""

    def computeDiff(ob1, ob2):
        """Compute the differences from ob1 to ob2 (ie. ob2 - ob1).

        The result will be a list of objects that implements the
        IDifference interface and represent the differences between
        ob1 and ob2."""

    def createChangeSet(ob1, ob2):
        """Returns a ChangeSet object that represents the differences
        between ob1 and ob2 (ie. ob2 - ob1) ."""



class IDifference(Interface):
    """An interface for interacting with the difference between two
    objects"""

    meta_type = Attribute('title', 'A human readable name for the diff type')
    field = Attribute('field', 'The name of the field being compared')
    same = Attribute('same', 'True if the fields are the "same" (whatever that means for this difference)')
    oldValue = Attribute('oldValue', 'The old field value being compared')
    newValue = Attribute('newValue', 'The new field value being compared')
    oldFilename = Attribute('oldFilename', 'The old filename for the field being compared')
    newFilename = Attribute('newFilename', 'The new filename for the field being compared')

    def testChanges(ob):
        """Test the specified object to determine if the change set will apply cleanly.

        Returns None if there would be no erros
        """

    def applyChanges(ob):
        """Update the specified object with the difference"""

    def filenameTitle(self, filename):
        """Translate the filename leading text
        """


class IStringDifference(IDifference):
    """An anterface for interacting with the difference between two
    string (text) objects"""

    def getLineDiffs():
        """Return a list of differences between the two objects on a
        line-by-line basis

        Each difference is a 5-tuple as described here:
        http://www.python.org/doc/2.1.3/lib/sequence-matcher.html#l2h-721

        The interpretation of these tuples depends on the difference class"""

##     def getCharDiffs():
##         """Return a list of character differences on a line-by-line basis.

##         For every line in the field being compared, return a list of
##         character differences """


class IChangeSet(Interface):
    """And interface representing all of the differences between two objects"""

    same = Attribute('same', 'True if the fields are the "same"')

    def computeDiff(ob1, ob2, recursive=1, exclude=None):
        """Compute the differences from ob1 to ob2 (ie. ob2 - ob1).

        If resursive is 1, compute differences between subobjects of
        ob1 and ob2 as well, excluding any subobjects whose IDs are
        listed in exclude

        The results can be accessed through getDiffs()"""

    def testChanges(ob):
        """Test the specified object to determine if the change set will apply cleanly.

        Returns None if there would be no erros
        """

    def applyChanges(ob):
        """Apply the computed changes to the specified object"""

    def getDiffs():
        """Returns the list of differences between the two objects.

        Each difference is a single object implementing the IDifference interface"""

    def getSubDiffs():
        """If the ChangeSet was computed recursively, returns a list
           of ChangeSet objects representing subobject differences

           Each ChangeSet will have the same ID as the objects whose
           difference it represents.
           """

    def getAddedItems():
        """If the ChangeSet was computed recursively, returns the list
        of IDs of items that were added.

        A copy of these items is available as a cubject of the ChangeSet
        """

    def getRemovedItems():
        """If the ChangeSet was computed recursively, returns the list
        of IDs of items that were removed"""

