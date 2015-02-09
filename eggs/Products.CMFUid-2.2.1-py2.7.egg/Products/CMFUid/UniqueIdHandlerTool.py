##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Unique Id Handler Tool

Provides support for accessing unique ids on content object.

$Id: UniqueIdHandlerTool.py 110665 2010-04-08 16:12:03Z tseaver $
"""

import logging
import Missing
import os

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from App.Common import package_home
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.component import getUtility
from zope.interface import implements

from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import UniqueObject
from Products.CMFUid.interfaces import IUniqueIdAnnotationManagement
from Products.CMFUid.interfaces import IUniqueIdBrainQuery
from Products.CMFUid.interfaces import IUniqueIdGenerator
from Products.CMFUid.interfaces import IUniqueIdHandler
from Products.CMFUid.interfaces import IUniqueIdUnrestrictedQuery
from Products.CMFUid.interfaces import UniqueIdError

UID_ATTRIBUTE_NAME = 'cmf_uid'

_wwwdir = os.path.join( package_home( globals() ), 'www' )


class UniqueIdHandlerTool(UniqueObject, SimpleItem):

    __doc__ = __doc__ # copy from module

    implements(IUniqueIdHandler, IUniqueIdBrainQuery,
               IUniqueIdUnrestrictedQuery)

    id = 'portal_uidhandler'

    manage_options = ( ({'label': 'Query',
                         'action': 'manage_queryObject'},)
                     + SimpleItem.manage_options
                     )

    alternative_id = "portal_standard_uidhandler"
    meta_type = 'Unique Id Handler Tool'

    # make the uid attribute name available for the unit tests
    # not meant to be altered as long you don't know what you do!!!
    UID_ATTRIBUTE_NAME = UID_ATTRIBUTE_NAME

    # make the exception class available through the tool
    UniqueIdError = UniqueIdError

    security = ClassSecurityInfo()

    def _reindexObject(self, obj):
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool
        catalog = getToolByName(self, 'portal_catalog')
        catalog.reindexObject(obj, idxs=[self.UID_ATTRIBUTE_NAME])

    def _setUid(self, obj, uid):
        """Attaches a unique id to the object and does reindexing.
        """
        # attach a unique id annotation to the object
        anno_tool = getUtility(IUniqueIdAnnotationManagement)
        annotation = anno_tool(obj, self.UID_ATTRIBUTE_NAME)
        annotation.setUid(uid)

        # reindex the object
        try:
            obj.reindexObject()
        except AttributeError:
            self._reindexObject(obj)

    security.declarePublic('register')
    def register(self, obj):
        """See IUniqueIdSet.
        """
        uid = self.queryUid(obj, default=None)
        if uid is None:
            # generate a new unique id and set it
            generator = getUtility(IUniqueIdGenerator)
            uid = generator()
            self._setUid(obj, uid)

        return uid

    security.declareProtected(ManagePortal, 'unregister')
    def unregister(self, obj):
        """See IUniqueIdSet.
        """
        UID_ATTRIBUTE_NAME = self.UID_ATTRIBUTE_NAME
        if getattr(aq_base(obj), UID_ATTRIBUTE_NAME, None) is None:
            raise UniqueIdError, \
                  "No unique id available to be unregistered on %r" % obj

        # delete the uid and reindex
        delattr(obj, UID_ATTRIBUTE_NAME)
        self._reindexObject(obj)

    security.declarePublic('queryUid')
    def queryUid(self, obj, default=None):
        """See IUniqueIdQuery.
        """
        uid = getattr(aq_base(obj), self.UID_ATTRIBUTE_NAME, None)
        # If 'obj' is a content object the 'uid' attribute is usually a
        # callable object. If 'obj' is a catalog brain the uid attribute
        # is non callable and possibly equals the 'Missing.MV' value.
        if uid is Missing.MV or uid is None:
            return default
        if callable(uid):
            return uid()
        return uid

    security.declarePublic('getUid')
    def getUid(self, obj):
        """See IUniqueIdQuery.
        """
        uid = self.queryUid(obj, None)
        if uid is None:
            raise UniqueIdError, "No unique id available on %r" % obj
        return uid

    security.declarePrivate('setUid')
    def setUid(self, obj, uid, check_uniqueness=True):
        """See IUniqueIdSet.
        """
        # None is the only value a unique id shall never have!
        if uid is None:
            raise UniqueIdError, "It's forbidden to set a unique id to 'None'."

        # check for uniqueness if enabled
        if check_uniqueness:
            result = self.queryObject(uid)
            if result is not None and result != obj:
                if callable(uid):
                    uid = uid()
                raise UniqueIdError, \
                      "The unique id '%s' is already in use" % uid

        # everything is ok: set it!
        self._setUid(obj, uid)

    def _queryBrain(self, uid, searchMethodName, default=None):
        """This helper method does the "hard work" of querying the catalog
           and interpreting the results.
        """
        # XXX: this method violates the rules for tools/utilities:
        # it depends on a non-utility tool
        if uid is None:
            return default

        # convert the uid to the right format
        generator = getUtility(IUniqueIdGenerator)
        uid = generator.convert(uid)

        catalog = getToolByName(self, 'portal_catalog')
        searchMethod = getattr(catalog, searchMethodName)
        result = searchMethod({self.UID_ATTRIBUTE_NAME: uid})
        len_result = len(result)

        # return None if no object found with this uid
        if len_result == 0:
            return default

        # print a message to the log  if more than one object has
        # the same uid (uups!)
        if len_result > 1:
            logging.getLogger('CMFUid').error(
                "ASSERT: %d objects have %r as uid!!!", len_result, uid)

        return result[0]

    security.declarePublic('queryBrain')
    def queryBrain(self, uid, default=None):
        """See IUniqueIdBrainQuery.
        """
        return self._queryBrain(uid, 'searchResults', default)

    def _getBrain(self, uid, queryBrainMethod):
        brain = queryBrainMethod(uid, default=None)
        if brain is None:
            raise UniqueIdError, "No object found with '%s' as uid." % uid
        return brain

    security.declarePublic('getBrain')
    def getBrain(self, uid):
        """See IUniqueIdBrainQuery.
        """
        return self._getBrain(uid, self.queryBrain)

    security.declarePublic('getObject')
    def getObject(self, uid):
        """See IUniqueIdQuery.
        """
        return self.getBrain(uid).getObject()

    security.declarePublic('queryObject')
    def queryObject(self, uid, default=None):
        """See IUniqueIdQuery.
        """
        try:
            return self.getObject(uid)
        except UniqueIdError:
            return default

    security.declarePrivate('unrestrictedQueryBrain')
    def unrestrictedQueryBrain(self, uid, default=None):
        """See IUniqueIdUnrestrictedQuery.
        """
        return self._queryBrain(uid, 'unrestrictedSearchResults', default)

    security.declarePrivate('unrestrictedGetBrain')
    def unrestrictedGetBrain(self, uid):
        """See IUniqueIdUnrestrictedQuery.
        """
        return self._getBrain(uid, self.unrestrictedQueryBrain)

    security.declarePrivate('unrestrictedGetObject')
    def unrestrictedGetObject(self, uid):
        """See IUniqueIdUnrestrictedQuery.
        """
        return self.unrestrictedGetBrain(uid).getObject()

    security.declarePrivate('unrestrictedQueryObject')
    def unrestrictedQueryObject(self, uid, default=None):
        """See IUniqueIdUnrestrictedQuery.
        """
        try:
            return self.unrestrictedGetObject(uid)
        except UniqueIdError:
            return default

    security.declareProtected(ManagePortal, 'manage_queryObject')
    manage_queryObject = PageTemplateFile('queryUID.pt', _wwwdir)

InitializeClass(UniqueIdHandlerTool)
