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

__version__='$Revision: 1.14 $'[11:-2]

import time
from random import randint

from Acquisition import Implicit, aq_parent, aq_inner
from ZopeVersionHistory import ZopeVersionHistory
from App.class_init import default__class_init__ as InitializeClass
from Persistence import Persistent
from AccessControl import ClassSecurityInfo
from Utility import use_vc_permission, _findPath
from Utility import isAVersionableResource, VersionControlError, VersionInfo
from DateTime.DateTime import DateTime
from BTrees.OOBTree import OOBTree
from BTrees.OIBTree import OIBTree

from EventLog import LogEntry
import Utility
from nonversioned import getNonVersionedData, restoreNonVersionedData


class Repository(Implicit, Persistent):
    """The repository implementation manages the actual data of versions
       and version histories. It does not handle user interface issues."""

    def __init__(self):
        # These keep track of symbolic label and branch names that
        # have been used to ensure that they don't collide.
        self._branches = OIBTree()
        self._branches['mainline'] = 1
        self._labels = OIBTree()

        self._histories = OOBTree()
        self._created = time.time()

    security = ClassSecurityInfo()

    security.declarePrivate('createVersionHistory')
    def createVersionHistory(self, object):
        """Internal: create a new version history for a resource."""
        # When one creates the first version in a version history, neither
        # the version or version history yet have a _p_jar, which causes
        # copy operations to fail. To work around that, we share our _p_jar.
        history_id = None
        while history_id is None or self._histories.has_key(history_id):
            history_id = str(randint(1, 9999999999))
        history = ZopeVersionHistory(history_id, object)
        self._histories[history_id] = history
        return history.__of__(self)

    security.declarePrivate('getVersionHistory')
    def getVersionHistory(self, history_id):
        """Internal: return a version history given a version history id."""
        return self._histories[history_id].__of__(self)

    security.declarePrivate('replaceState')
    def replaceState(self, obj, new_state):
        """Internal: replace the state of a persistent object.
        """
        non_versioned = getNonVersionedData(obj)
        # XXX There ought to be some way to do this more cleanly.
        # This fills the __dict__ of the old object with new state.
        # The other way to achieve the desired effect is to replace
        # the object in its container, but this method preserves the
        # identity of the object.
        if obj.__class__ is not new_state.__class__:
            raise VersionControlError(
                "The class of the versioned object has changed. %s != %s"
                % (repr(obj.__class__, new_state.__class__)))
        obj._p_changed = 1
        for key in obj.__dict__.keys():
            if not new_state.__dict__.has_key(key):
                del obj.__dict__[key]
        for key, value in new_state.__dict__.items():
            obj.__dict__[key] = value
        if non_versioned:
            # Restore the non-versioned data into the new state.
            restoreNonVersionedData(obj, non_versioned)
        return obj

    #####################################################################
    # This is the implementation of the public version control interface.
    #####################################################################

    security.declarePublic('isAVersionableResource')
    def isAVersionableResource(self, obj):
        # For now, an object must be persistent (have its own db record)
        # in order to be considered a versionable resource.
        return isAVersionableResource(obj)

    security.declarePublic('isUnderVersionControl')
    def isUnderVersionControl(self, object):
        return hasattr(object, '__vc_info__')

    security.declarePublic('isResourceUpToDate')
    def isResourceUpToDate(self, object, require_branch=0):
        info = self.getVersionInfo(object)
        history = self.getVersionHistory(info.history_id)
        branch = 'mainline'
        if info.sticky:
            if info.sticky[0] == 'B':
                branch = info.sticky[1]
            elif require_branch:
                # The object is updated to a particular version
                # rather than a branch.  The caller
                # requires a branch.
                return 0
        return history.isLatestVersion(info.version_id, branch)

    security.declarePublic('isResourceChanged')
    def isResourceChanged(self, object):
        # Return true if the state of a resource has changed in a transaction
        # *after* the version bookkeeping was saved. Note that this method is
        # not appropriate for detecting changes within a transaction!
        info = self.getVersionInfo(object)
        itime = getattr(info, '_p_mtime', None)
        if itime is None:
            return 0
        mtime = Utility._findModificationTime(object)
        if mtime is None:
            return 0
        return mtime > itime

    security.declarePublic('getVersionInfo')
    def getVersionInfo(self, object):
        info = getattr(object, '__vc_info__', None)
        if info is not None:
            return info
        raise VersionControlError(
            'The specified resource is not under version control.'
            )

    security.declareProtected(use_vc_permission, 'applyVersionControl')
    def applyVersionControl(self, object, message=None):
        if self.isUnderVersionControl(object):
            raise VersionControlError(
                'The resource is already under version control.'
                )
        if not self.isAVersionableResource(object):
            raise VersionControlError(
                'This resource cannot be put under version control.'
                )

        # Need to check the parent to see if the container of the object
        # being put under version control is itself a version-controlled
        # object. If so, we need to use the branch id of the container.
        branch = 'mainline'
        parent = aq_parent(aq_inner(object))
        p_info = getattr(parent, '__vc_info__', None)
        if p_info is not None:
            sticky = p_info.sticky
            if sticky and sticky[0] == 'B':
                branch = sticky[1]

        # Create a new version history and initial version object.
        history = self.createVersionHistory(object)
        version = history.createVersion(object, branch)

        history_id = history.getId()
        version_id = version.getId()

        # Add bookkeeping information to the version controlled object.
        info = VersionInfo(history_id, version_id, VersionInfo.CHECKED_IN)
        if branch != 'mainline':
            info.sticky = ('B', branch)
        object.__vc_info__ = info

        # Save an audit record of the action being performed.
        history.addLogEntry(version_id,
                            LogEntry.ACTION_CHECKIN,
                            _findPath(object),
                            message is None and 'Initial checkin.' or message
                            )
        return object

    security.declareProtected(use_vc_permission, 'checkoutResource')
    def checkoutResource(self, object):
        info = self.getVersionInfo(object)
        if info.status != info.CHECKED_IN:
            raise VersionControlError(
                'The selected resource is already checked out.'
                )

        if info.sticky and info.sticky[0] != 'B':
            raise VersionControlError(
                'The selected resource has been updated to a particular '
                'version, label or date. The resource must be updated to '
                'the mainline or a branch before it may be checked out.'
                )

        if not self.isResourceUpToDate(object):
            raise VersionControlError(
                'The selected resource is not up to date!'
                )

        history = self.getVersionHistory(info.history_id)
        ob_path = _findPath(object)

        # Save an audit record of the action being performed.
        history.addLogEntry(info.version_id,
                            LogEntry.ACTION_CHECKOUT,
                            ob_path
                            )

        # Update bookkeeping information.
        newinfo = info.clone()
        newinfo.status = newinfo.CHECKED_OUT
        object.__vc_info__ = newinfo
        return object

    security.declareProtected(use_vc_permission, 'checkinResource')
    def checkinResource(self, object, message=''):
        info = self.getVersionInfo(object)
        if info.status != info.CHECKED_OUT:
            raise VersionControlError(
                'The selected resource is not checked out.'
                )

        if info.sticky and info.sticky[0] != 'B':
            raise VersionControlError(
                'The selected resource has been updated to a particular '
                'version, label or date. The resource must be updated to '
                'the mainline or a branch before it may be checked in.'
                )

        if not self.isResourceUpToDate(object):
            raise VersionControlError(
                'The selected resource is not up to date!'
                )

        history = self.getVersionHistory(info.history_id)
        ob_path = _findPath(object)

        branch = 'mainline'
        if info.sticky is not None and info.sticky[0] == 'B':
            branch = info.sticky[1]

        version = history.createVersion(object, branch)

        # Save an audit record of the action being performed.
        history.addLogEntry(version.getId(),
                            LogEntry.ACTION_CHECKIN,
                            ob_path,
                            message
                            )

        # Update bookkeeping information.
        newinfo = info.clone()
        newinfo.version_id = version.getId()
        newinfo.status = newinfo.CHECKED_IN
        object.__vc_info__ = newinfo
        return object

    security.declareProtected(use_vc_permission, 'uncheckoutResource')
    def uncheckoutResource(self, object):
        info = self.getVersionInfo(object)
        if info.status != info.CHECKED_OUT:
            raise VersionControlError(
                'The selected resource is not checked out.'
                )

        history = self.getVersionHistory(info.history_id)
        ob_path = _findPath(object)

        version = history.getVersionById(info.version_id)
        new_obj = version.copyState()

        # Save an audit record of the action being performed.
        history.addLogEntry(info.version_id,
                            LogEntry.ACTION_UNCHECKOUT,
                            ob_path
                            )

        # Replace the state of the object with a reverted state.
        new_obj = self.replaceState(object, new_obj)

        # Update bookkeeping information.
        newinfo = info.clone()
        newinfo.version_id = version.getId()
        newinfo.status = newinfo.CHECKED_IN
        new_obj.__vc_info__ = newinfo
        return new_obj

    security.declareProtected(use_vc_permission, 'updateResource')
    def updateResource(self, object, selector=None):
        info = self.getVersionInfo(object)
        if info.status != info.CHECKED_IN:
            raise VersionControlError(
                'The selected resource must be checked in to be updated.'
                )

        history = self.getVersionHistory(info.history_id)
        version = None
        sticky = info.sticky

        if not selector:
            # If selector is null, update to the latest version taking any
            # sticky attrs into account (branch, date). Note that the sticky
            # tag could also be a date or version id. We don't bother checking
            # for those, since in both cases we do nothing (because we'll
            # always be up to date until the sticky tag changes).
            if sticky and sticky[0] == 'L':
                # A label sticky tag, so update to that label (since it is
                # possible, but unlikely, that the label has been moved).
                version = history.getVersionByLabel(sticky[1])
            elif sticky and sticky[0] == 'B':
                # A branch sticky tag. Update to latest version on branch.
                version = history.getLatestVersion(selector)
            else:
                # Update to mainline, forgetting any date or version id
                # sticky tag that was previously associated with the object.
                version = history.getLatestVersion('mainline')
                sticky = None
        else:
            # If the selector is non-null, we find the version specified
            # and update the sticky tag. Later we'll check the version we
            # found and decide whether we really need to update the object.
            if history.hasVersionId(selector):
                version = history.getVersionById(selector)
                sticky = ('V', selector)

            elif self._labels.has_key(selector):
                version = history.getVersionByLabel(selector)
                sticky = ('L', selector)

            elif self._branches.has_key(selector):
                version = history.getLatestVersion(selector)
                if selector == 'mainline':
                    sticky = None
                else:
                    sticky = ('B', selector)
            else:
                try:    date = DateTime(selector)
                except:
                    raise VersionControlError(
                        'Invalid version selector: %s' % selector
                        )
                else:
                    timestamp = date.timeTime()
                    sticky = ('D', timestamp)
                    # Fix!
                    branch = history.findBranchId(info.version_id)
                    version = history.getVersionByDate(branch, timestamp)

        # If the state of the resource really needs to be changed, do the
        # update and make a log entry for the update.
        version_id = version and version.getId() or info.version_id
        new_object = object
        if version and (version_id != info.version_id):
            new_object = version.copyState()
            new_object = self.replaceState(object, new_object)

            history.addLogEntry(version_id,
                                LogEntry.ACTION_UPDATE,
                                _findPath(new_object)
                                )

        # Update bookkeeping information.
        newinfo = info.clone(1)
        newinfo.version_id = version_id
        newinfo.status = newinfo.CHECKED_IN
        if sticky is not None:
            newinfo.sticky = sticky
        new_object.__vc_info__ = newinfo
        return new_object

    security.declareProtected(use_vc_permission, 'labelResource')
    def labelResource(self, object, label, force=0):
        info = self.getVersionInfo(object)
        if info.status != info.CHECKED_IN:
            raise VersionControlError(
                'The selected resource must be checked in to be labeled.'
                )

        # Make sure that labels and branch ids do not collide.
        if self._branches.has_key(label) or label == 'mainline':
            raise VersionControlError(
                'The label value given is already in use as an activity id.'
                )
        if not self._labels.has_key(label):
            self._labels[label] = 1

        history = self.getVersionHistory(info.history_id)
        history.labelVersion(info.version_id, label, force)
        return object

    security.declareProtected(use_vc_permission, 'makeActivity')
    def makeActivity(self, object, branch_id):
        # Note - this is not part of the official version control API yet.
        # It is here to allow unit testing of the architectural aspects
        # that are already in place to support activities in the future.

        info = self.getVersionInfo(object)
        if info.status != info.CHECKED_IN:
            raise VersionControlError(
                'The selected resource must be checked in.'
                )

        branch_id = branch_id or None

        # Make sure that activity ids and labels do not collide.
        if self._labels.has_key(branch_id) or branch_id == 'mainline':
            raise VersionControlError(
                'The value given is already in use as a version label.'
                )

        if not self._branches.has_key(branch_id):
            self._branches[branch_id] = 1

        history = self.getVersionHistory(info.history_id)

        if history._branches.has_key(branch_id):
            raise VersionControlError(
                'The resource is already associated with the given activity.'
                )

        history.createBranch(branch_id, info.version_id)
        return object

    security.declareProtected(use_vc_permission, 'getVersionOfResource')
    def getVersionOfResource(self, history_id, selector):
        history = self.getVersionHistory(history_id)
        sticky = None

        if not selector or selector == 'mainline':
            version = history.getLatestVersion('mainline')
        else:
            if history.hasVersionId(selector):
                version = history.getVersionById(selector)
                sticky = ('V', selector)

            elif self._labels.has_key(selector):
                version = history.getVersionByLabel(selector)
                sticky = ('L', selector)

            elif self._branches.has_key(selector):
                version = history.getLatestVersion(selector)
                sticky = ('B', selector)
            else:
                try: date = DateTime(selector)
                except:
                    raise VersionControlError(
                        'Invalid version selector: %s' % selector
                        )
                else:
                    timestamp = date.timeTime()
                    sticky = ('D', timestamp)
                    version = history.getVersionByDate('mainline', timestamp)

        object = version.copyState()

        info = VersionInfo(history_id, version.getId(), VersionInfo.CHECKED_IN)
        if sticky is not None:
            info.sticky = sticky
        object.__vc_info__ = info
        return object

    security.declareProtected(use_vc_permission, 'getVersionIds')
    def getVersionIds(self, object):
        info = self.getVersionInfo(object)
        history = self.getVersionHistory(info.history_id)
        return history.getVersionIds()

    security.declareProtected(use_vc_permission, 'getLabelsForResource')
    def getLabelsForResource(self, object):
        info = self.getVersionInfo(object)
        history = self.getVersionHistory(info.history_id)
        return history.getLabels()

    security.declareProtected(use_vc_permission, 'getLogEntries')
    def getLogEntries(self, object):
        info = self.getVersionInfo(object)
        history = self.getVersionHistory(info.history_id)
        return history.getLogEntries()

InitializeClass(Repository)
