##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

__version__='$Revision: 1.7 $'[11:-2]

from zope.interface import Interface


class IVersionControl(Interface):
    """The version control interface serves as the main API for version 
       control operations. The interface hides most of the details of
       version data storage and retrieval.

       In Zope 3, the version control interface will probably be implemented
       by a version control service. In the meantime, it may be implemented
       directly by repository implementations (or other things, like CMF
       tools).

       The goal of this version of the version control interface is to
       support simple linear versioning with support for labelled versions.
       Future versions or extensions of this interface will likely support 
       more advanced version control features such as concurrent lines of
       descent (activities) and collection versioning."""

    def isAVersionableResource(object):
        """
        Returns true if the given object is a versionable resource.

        Permission: public
        """

    def isUnderVersionControl(object):
        """
        Returns true if the given object is under version control.

        Permission: public
        """

    def isResourceUpToDate(object, require_branch=0):
        """
        Returns true if a resource is based on the latest version. Note
        that the latest version is in the context of any activity (branch).

        If the require_branch flag is true, this method returns false if
        the resource is updated to a particular version, label, or date.
        Useful for determining whether a call to checkoutResource()
        will succeed.

        Permission: public
        """

    def isResourceChanged(object):
        """
        Return true if the state of a resource has changed in a transaction
        *after* the version bookkeeping was saved. Note that this method is 
        not appropriate for detecting changes within a transaction!

        Permission: public
        """

    def getVersionInfo(object):
        """
        Return the VersionInfo associated with the given object. The
        VersionInfo object contains version control bookkeeping information.
        If the object is not under version control, a VersionControlError
        will be raised.

        Permission: public
        """

    def applyVersionControl(object, message=None):
        """
        Place the given object under version control. A VersionControlError
        will be raised if the object is already under version control.

        After being placed under version control, the resource is logically
        in the 'checked-in' state.

        If no message is passed the 'Initial checkin.' message string is 
        written as the message log entry.

        Permission: Use version control
        """

    def checkoutResource(object):
        """
        Put the given version-controlled object into the 'checked-out'
        state, allowing changes to be made to the object. If the object is
        not under version control or the object is already checked out, a
        VersionControlError will be raised.

        Permission: Use version control
        """

    def checkinResource(object, message=''):
        """
        Check-in (create a new version) of the given object, updating the
        state and bookkeeping information of the given object. The optional
        message should describe the changes being committed. If the object
        is not under version control or is already in the checked-in state,
        a VersionControlError will be raised.

        Permission: Use version control
        """

    def uncheckoutResource(object):
        """
        Discard changes to the given object made since the last checkout.
        If the object is not under version control or is not checked out,
        a VersionControlError will be raised.
        """

    def updateResource(object, selector=None):
        """
        Update the state of the given object to that of a specific version
        of the object. The object must be in the checked-in state to be
        updated. The selector must be a string (version id, activity id,
        label or date) that is used to select a version from the version
        history.

        Permission: Use version control
        """

    def labelResource(object, label, force=None):
        """
        Associate the given resource with a label. If force is true, then
        any existing association with the given label will be removed and
        replaced with the new association. If force is false and there is
        an existing association with the given label, a VersionControlError
        will be raised.

        Permission: Use version control
        """

    def getVersionOfResource(history_id, selector):
        """
        Given a version history id and a version selector, return the
        object as of that version. Note that the returned object has no
        acquisition context. The selector must be a string (version id,
        activity id, label or date) that is used to select a version
        from the version history.

        Permission: Use version control
        """

    def getVersionIds(object):
        """
        Return a sequence of the (string) version ids corresponding to the
        available versions of an object. This should be used by UI elements
        to populate version selection widgets, etc.

        Permission: Use version control
        """

    def getLabelsForResource(object):
        """
        Return a sequence of the (string) labels corresponding to the
        versions of the given object that have been associated with a
        label. This should be used by UI elements to populate version
        selection widgets, etc.

        Permission: Use version control
        """

    def getLogEntries(object):
        """
        Return a sequence of LogEntry objects (most recent first) that
        are associated with a version-controlled object.

        Permission: Use version control
        """

class IVersionInfo(Interface):
    """The IVersionInfo interface provides access to version control
       bookkeeping information. The fields provided by this interface
       are:

         timestamp - a float (time.time() format) value indicating the
         time that the bookkeeping information was created.

         history_id - the id of the version history related to the version
         controlled resource.
         
         version_id - the version id that the version controlled resource
         is based upon.

         status - an enumerated value indicating the status of the version
         controlled resource. This value is one of the VersionInfo class
         constants CHECKED_IN or CHECKED_OUT.

         sticky - sticky tag information used internally by the version
         control implementation.

         user_id - the id of the effective user at the time the bookkeeping
         information was created.
         """

class ILogEntry(Interface):
    """The ILogEntry interface provides access to the information in an
       audit log entry. The fields provided by this interface are:

         timestamp - a float (time.time() format) value indicating the
         time that the log entry was created.

         version_id - the version id of the version controlled resource
         related to the log entry.

         action - an enumerated value indicating the action that was taken.
         This value is one of the LogEntry class constants ACTION_CHECKOUT,
         ACTION_CHECKIN, ACTION_UNCHECKOUT, ACTION_UPDATE.

         message - a string message provided by the user at the time of the
         action. This string may be empty.

         user_id - the id of the user causing the audited action.

         path - the path to the object upon which the action was taken.

         """


class INonVersionedData(Interface):
    """Controls what parts of an object fall outside version control.

    Containerish objects implement this interface to allow the items they
    contain to be versioned independently of the container.
    """

    def listNonVersionedObjects():
        """Returns a list of subobjects that should not be pickled.

        The objects in the list must not be wrapped, because only the
        identity of the objects will be considered.  The version
        repository uses this method to avoid cloning subobjects that
        will soon be removed by removeNonVersionedData.
        """

    def removeNonVersionedData():
        """Removes the non-versioned data from this object.

        The version repository uses this method before storing an
        object in the version repository.
        """

    def getNonVersionedData():
        """Returns an opaque object containing the non-versioned data.

        The version repository uses this method before reverting an
        object to a revision.
        """

    def restoreNonVersionedData(dict):
        """Restores non-versioned data to this object.

        The version repository uses this method after reverting an
        object to a revision.
        """

IVersionedContainer = INonVersionedData
