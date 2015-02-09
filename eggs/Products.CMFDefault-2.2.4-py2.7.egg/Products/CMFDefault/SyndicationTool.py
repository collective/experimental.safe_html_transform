##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" CMFDefault portal_syndication tool.

Manage outbound RSS syndication of folder content. """

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from App.special_dtml import HTMLFile
from DateTime.DateTime import DateTime
from OFS.SimpleItem import SimpleItem
from zope.interface import implements

from Products.CMFCore.interfaces import ISyndicationTool
from Products.CMFCore.PortalFolder import PortalFolderBase
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import UniqueObject
from Products.CMFDefault.exceptions import AccessControl_Unauthorized
from Products.CMFDefault.permissions import ManagePortal
from Products.CMFDefault.permissions import ManageProperties
from Products.CMFDefault.SyndicationInfo import SyndicationInformation
from Products.CMFDefault.utils import _dtmldir


class SyndicationTool(UniqueObject, SimpleItem):
    """ The syndication tool manages the site-wide policy for
        syndication of folder content as RSS.
    """
    implements(ISyndicationTool)

    id = 'portal_syndication'
    meta_type = 'Default Syndication Tool'

    security = ClassSecurityInfo()

    #Default Sitewide Values
    isAllowed = 0
    syUpdatePeriod = 'daily'
    syUpdateFrequency = 1
    syUpdateBase = DateTime()
    max_items = 15

    #ZMI Methods
    manage_options = ( ( { 'label'  : 'Overview'
                         , 'action' : 'overview'
                         , 'help'   : ( 'CMFDefault'
                                      , 'Syndication-Tool_Overview.stx' )
                         }
                        ,{ 'label'  : 'Properties'
                         , 'action' : 'propertiesForm'
                         , 'help'   : ( 'CMFDefault'
                                      , 'Syndication-Tool_Properties.stx' )
                         }
                        ,{ 'label'  : 'Policies'
                         , 'action' : 'policiesForm'
                         , 'help'   : ( 'CMFDefault'
                                      , 'Syndication-Tool_Policies.stx' )
                         }
                        ,{ 'label'  : 'Reports'
                         , 'action' : 'reportForm'
                         , 'help'   : ( 'CMFDefault'
                                      , 'Syndication-Tool_Reporting.stx' )
                         }
                        )
                     )

    security.declareProtected(ManagePortal, 'overview')
    overview = HTMLFile('synOverview', _dtmldir)

    security.declareProtected(ManagePortal, 'propertiesForm')
    propertiesForm = HTMLFile('synProps', _dtmldir)

    security.declareProtected(ManagePortal, 'policiesForm')
    policiesForm = HTMLFile('synPolicies', _dtmldir)

    security.declareProtected(ManagePortal, 'reportForm')
    reportForm = HTMLFile('synReports', _dtmldir)

    security.declareProtected(ManagePortal, 'editProperties')
    def editProperties( self
                      , updatePeriod=None
                      , updateFrequency=None
                      , updateBase=None
                      , isAllowed=None
                      , max_items=None
                      , REQUEST=None
                      ):
        """
        Edit the properties for the SystemWide defaults on the
        SyndicationTool.
        """
        if isAllowed is not None:
            self.isAllowed = isAllowed

        if updatePeriod is not None:
            self.syUpdatePeriod = updatePeriod
        else:
            try:
                del self.syUpdatePeriod
            except (AttributeError, KeyError):
                pass

        if updateFrequency is not None:
            self.syUpdateFrequency = int(updateFrequency)
        else:
            try:
                del self.syUpdateFrequency
            except (AttributeError, KeyError):
                pass

        if updateBase is not None:
            if type( updateBase ) is type( '' ):
                updateBase = DateTime( updateBase )
            self.syUpdateBase = updateBase
        else:
            try:
                del self.syUpdateBase
            except (AttributeError, KeyError):
                pass

        if max_items is not None:
            self.max_items = int(max_items)
        else:
            try:
                del self.max_items
            except (AttributeError, KeyError):
                pass

        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect( self.absolute_url()
                                        + '/propertiesForm'
                                        + '?manage_tabs_message=Tool+Updated.'
                                        )

    security.declarePublic( 'editSyInformationProperties' )
    def editSyInformationProperties( self
                                   , obj
                                   , updatePeriod=None
                                   , updateFrequency=None
                                   , updateBase=None
                                   , max_items=None
                                   , REQUEST=None
                                   ):
        """
        Edit syndication properties for the obj being passed in.
        These are held on the syndication_information object.
        Not Sitewide Properties.
        """
        if not _checkPermission( ManageProperties, obj ):
            raise AccessControl_Unauthorized

        syInfo = getattr(obj, 'syndication_information', None)

        if syInfo is None:
            raise 'Syndication is Disabled'

        if updatePeriod is not None:
            syInfo.syUpdatePeriod = updatePeriod
        else:
            syInfo.syUpdatePeriod = self.syUpdatePeriod

        if updateFrequency is not None:
            syInfo.syUpdateFrequency = int(updateFrequency)
        else:
            syInfo.syUpdateFrequency = self.syUpdateFrequency

        if updateBase is not None:
            if type( updateBase ) is type( '' ):
                updateBase = DateTime( updateBase )
            syInfo.syUpdateBase = updateBase
        else:
            syInfo.syUpdateBase = self.syUpdateBase

        if max_items is not None:
            syInfo.max_items = int(max_items)
        else:
            syInfo.max_items = self.max_items

    security.declarePublic('enableSyndication')
    def enableSyndication(self, obj):
        """
        Enable syndication for the obj
        """
        if not self.isSiteSyndicationAllowed():
            raise 'Syndication is Disabled'

        if hasattr(aq_base(obj), 'syndication_information'):
            raise 'Syndication Information Exists'

        syInfo = SyndicationInformation()
        obj._setObject('syndication_information', syInfo)
        syInfo = obj._getOb('syndication_information')
        syInfo.syUpdatePeriod = self.syUpdatePeriod
        syInfo.syUpdateFrequency = self.syUpdateFrequency
        syInfo.syUpdateBase = self.syUpdateBase
        syInfo.max_items = self.max_items
        syInfo.description = "Channel Description"

    security.declarePublic('disableSyndication')
    def disableSyndication(self, obj):
        """
        Disable syndication for the obj; and remove it.
        """
        syInfo = getattr(obj, 'syndication_information', None)

        if syInfo is None:
            raise 'This object does not have Syndication Information'

        obj._delObject('syndication_information')

    security.declarePublic('getSyndicatableContent')
    def getSyndicatableContent(self, obj):
        """
        An interface for allowing folderish items to implement an
        equivalent of PortalFolderBase.contentValues()
        """
        if hasattr(obj, 'synContentValues'):
            values = obj.synContentValues()
        else:
            values = PortalFolderBase.contentValues(obj)
        return values

    security.declarePublic('buildUpdatePeriods')
    def buildUpdatePeriods(self):
        """
        Return a list of possible update periods for the xmlns: sy
        """
        updatePeriods = ( ('hourly',  'Hourly')
                        , ('daily',   'Daily')
                        , ('weekly',  'Weekly')
                        , ('monthly', 'Monthly')
                        , ('yearly',  'Yearly')
                        )
        return updatePeriods

    security.declarePublic('isSiteSyndicationAllowed')
    def isSiteSyndicationAllowed(self):
        """
        Return sitewide syndication policy
        """
        return self.isAllowed

    security.declarePublic('isSyndicationAllowed')
    def isSyndicationAllowed(self, obj=None):
        """
        Check whether syndication is enabled for the site.  This
        provides for extending the method to check for whether a
        particular obj is enabled, allowing for turning on only
        specific folders for syndication.
        """
        syInfo = getattr(aq_base(obj), 'syndication_information',
                         None)
        if syInfo is None:
            return 0
        else:
            return self.isSiteSyndicationAllowed()

    security.declarePublic('getUpdatePeriod')
    def getUpdatePeriod( self, obj=None ):
        """
        Return the update period for the RSS syn namespace.
        This is either on the object being passed or the
        portal_syndication tool (if a sitewide value or default
        is set)

        NOTE:  Need to add checks for sitewide policies!!!
        """
        if not self.isSiteSyndicationAllowed():
            raise 'Syndication is Not Allowed'

        if obj is None:
            return self.syUpdatePeriod

        syInfo = getattr(obj, 'syndication_information', None)

        if syInfo is not None:
            return syInfo.syUpdatePeriod
        else:
            return 'Syndication is Not Allowed'

    security.declarePublic('getUpdateFrequency')
    def getUpdateFrequency(self, obj=None):
        """
        Return the update frequency (as a positive integer) for
        the syn namespace.  This is either on the object being
        pass or the portal_syndication tool (if a sitewide value
        or default is set).

        Note:  Need to add checks for sitewide policies!!!
        """
        if not self.isSiteSyndicationAllowed():
            raise 'Syndication is not Allowed'

        if obj is None:
            return self.syUpdateFrequency

        syInfo = getattr(obj, 'syndication_information',
                            None)
        if syInfo is not None:
            return syInfo.syUpdateFrequency
        else:
            return 'Syndication is not Allowed'

    security.declarePublic('getUpdateBase')
    def getUpdateBase(self, obj=None):
        """
        Return the base date to be used with the update frequency
        and the update period to calculate a publishing schedule.

        Note:  I'm not sure what's best here, creation date, last
        modified date (of the folder being syndicated) or some
        arbitrary date.  For now, I'm going to build a updateBase
        time from zopetime and reformat it to meet the W3CDTF.
        Additionally, sitewide policy checks might have a place
        here...
        """
        if not self.isSiteSyndicationAllowed():
            raise 'Syndication is not Allowed'

        if obj is None:
            when = self.syUpdateBase
            return when.ISO()

        syInfo = getattr(obj, 'syndication_information',
                            None)
        if syInfo is not None:
                when = syInfo.syUpdateBase
                return when.ISO()
        else:
            return 'Syndication is not Allowed'

    security.declarePublic('getHTML4UpdateBase')
    def getHTML4UpdateBase(self, obj=None):
        """
        Return HTML4 formated UpdateBase DateTime
        """
        if not self.isSiteSyndicationAllowed():
            raise 'Syndication is not Allowed'

        if obj is None:
            when = self.syUpdateBase
            return when.HTML4()

        syInfo = getattr(obj, 'syndication_information',
                            None)
        if syInfo is not None:
            when = syInfo.syUpdateBase
            return when.HTML4()
        else:
            return 'Syndication is not Allowed'

    def getMaxItems(self, obj=None):
        """
        Return the max_items to be displayed in the syndication
        """
        if not self.isSiteSyndicationAllowed():
            raise 'Syndication is not Allowed'

        if obj is None:
            return self.max_items

        syInfo = getattr(obj, 'syndication_information',
                            None)
        if syInfo is not None:
            return syInfo.max_items
        else:
            return 'Syndication is not Allowed'

InitializeClass(SyndicationTool)
registerToolInterface('portal_syndication', ISyndicationTool)
