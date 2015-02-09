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

__version__='$Revision: 1.4 $'[11:-2]

import ExtensionClass, AccessControl, Acquisition
from App.class_init import default__class_init__ as InitializeClass
from App.special_dtml import DTMLFile
from Utility import VersionControlError, isAVersionableResource
from Utility import use_vc_permission


class VersionSupport(ExtensionClass.Base):
    """Mixin class to support version-controllable resources."""

    manage_options=(
        {'label': 'Version Control', 'action':'versionControlMain',
         'help':  ('ZopeVersionControl', 'VersionControl.stx'),
         'filter': isAVersionableResource,
         },
        )

    security = AccessControl.ClassSecurityInfo()

    security.declareProtected('View management screens', 'versionControlMain')
    versionControlMain = DTMLFile('dtml/VersionControlMain', globals())

    security.declareProtected('View management screens', 'versionControlLog')
    versionControlLog = DTMLFile('dtml/VersionControlLog', globals())

    security.declarePrivate('haveRepository')
    def haveRepository(self):
        try: result = self.getRepository()
        except VersionControlError:
            return 0
        return 1

    security.declarePrivate('getRepository')
    def getRepository(self):
        # We currently only allow a single repository in a given context.
        if hasattr(self, '_v_repository'):
            return self._v_repository
        try:    items = self.superValues('Repository')
        except: items = self.aq_inner.aq_parent.superValues('Repository')
        result = items and items[0] or None
        if result is None:
            raise VersionControlError(
                'No versioning repository was found.'
                )
        self._v_repository = result
        return result


    security.declarePublic('isAVersionableResource')
    def isAVersionableResource(self, object):
        return self.getRepository().isAVersionableResource(self)

    security.declarePublic('isUnderVersionControl')
    def isUnderVersionControl(self):
        return hasattr(self, '__vc_info__')

    security.declarePublic('isResourceUpToDate')
    def isResourceUpToDate(self):
        return self.getRepository().isResourceUpToDate(self)

    security.declarePublic('isResourceChanged')
    def isResourceChanged(self):
        return self.getRepository().isResourceChanged(self)

    security.declarePublic('getVersionInfo')
    def getVersionInfo(self):
        return self.getRepository().getVersionInfo(self)

    security.declareProtected(use_vc_permission, 'applyVersionControl')
    def applyVersionControl(self, REQUEST=None):
        """Place a resource under version control."""
        repository = self.getRepository()
        object = repository.applyVersionControl(self)
        if REQUEST is not None:
            message="The resource has been placed under version control."
            return object.versionControlMain(
                object, REQUEST,
                manage_tabs_message=message
                )

    security.declareProtected(use_vc_permission, 'checkoutResource')
    def checkoutResource(self, REQUEST=None):
        """Checkout a version-controlled resource."""
        repository = self.getRepository()
        object = repository.checkoutResource(self)
        if REQUEST is not None:
            message="The resource has been checked out."
            return object.versionControlMain(
                object, REQUEST,
                manage_tabs_message=message
                )

    security.declareProtected(use_vc_permission, 'checkinResource')
    def checkinResource(self, message='', REQUEST=None):
        """Checkout a version-controlled resource."""
        repository = self.getRepository()
        object = repository.checkinResource(self, message)
        version = object.getVersionInfo().version_id
        if REQUEST is not None:
            message="The resource has been checked in [version %s]." % version
            return object.versionControlMain(
                object, REQUEST,
                manage_tabs_message=message
                )

    security.declareProtected(use_vc_permission, 'uncheckoutResource')
    def uncheckoutResource(self, REQUEST=None):
        """Uncheckout a version-controlled resource."""
        repository = self.getRepository()
        object = repository.uncheckoutResource(self)
        version = object.getVersionInfo().version_id
        if REQUEST is not None:
            message="The resource has been reverted to version %s." % version
            return object.versionControlMain(
                object, REQUEST,
                manage_tabs_message=message
                )

    security.declareProtected(use_vc_permission, 'updateResource')
    def updateResource(self, selector, REQUEST=None):
        """Update a version-controlled resource."""
        repository = self.getRepository()
        if selector == 'LATEST_VERSION':
            selector = None
        object = repository.updateResource(self, selector)
        version = object.getVersionInfo().version_id
        if REQUEST is not None:
            message="The resource has been updated to version %s." % version
            return object.versionControlMain(
                object, REQUEST,
                manage_tabs_message=message
                )

    security.declareProtected(use_vc_permission, 'labelResource')
    def labelResource(self, label, force=0, REQUEST=None):
        """Label a version-controlled resource."""
        repository = self.getRepository()
        object = repository.labelResource(self, label, force)
        if REQUEST is not None:
            message="The label has been applied to this resource."
            return object.versionControlMain(
                object, REQUEST,
                manage_tabs_message=message
                )

    security.declareProtected(use_vc_permission, 'getVersionIds')
    def getVersionIds(self):
        return self.getRepository().getVersionIds(self)

    security.declareProtected(use_vc_permission, 'getLabelsForHistory')
    def getLabelsForHistory(self):
        return self.getRepository().getLabelsForHistory(self)

    security.declareProtected(use_vc_permission, 'getLabelsForVersion')
    def getLabelsForVersion(self):
        return self.getRepository().getLabelsForVersion(self)

    security.declareProtected(use_vc_permission, 'getLogEntries')
    def getLogEntries(self):
        return self.getRepository().getLogEntries(self)


InitializeClass(VersionSupport)


