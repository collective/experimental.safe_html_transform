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
""" Favorites are references to other objects within the same CMF site. """

import urlparse

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from zope.component import adapter
from zope.component import getUtility
from zope.component.factory import Factory
from zope.container.interfaces import IObjectAddedEvent
from zope.interface import implements

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFDefault.interfaces import IFavorite
from Products.CMFDefault.interfaces import IMutableFavorite
from Products.CMFDefault.Link import Link
from Products.CMFDefault.permissions import View


def addFavorite(self, id, title='', remote_url='', description=''):
    """Add a Favorite.
    """
    o = Favorite(id, title, remote_url, description)
    self._setObject(id, o, suppress_events=True)


class Favorite(Link):

    """A Favorite (special kind of Link).
    """

    implements(IMutableFavorite, IFavorite)

    security = ClassSecurityInfo()

    def __init__( self
                , id
                , title=''
                , remote_url=''
                , description=''
                ):
        DefaultDublinCoreImpl.__init__(self)
        self.id=id
        self.title=title
        self.remote_url=remote_url
        self.description = description

    def _getUidByUrl(self):
        """Registers and returns the uid of the remote object if
        the unique id handler tool is available.
        """
        # check for unique id handler tool
        handler = getToolByName(self, 'portal_uidhandler', None)
        if handler is None:
            return

        obj = getUtility(ISiteRoot).restrictedTraverse(self.remote_url)
        return handler.register(obj)

    def _getObjectByUid(self):
        """Registers and returns the uid of the remote object if
        the unique id handler tool is available.
        """
        # check for unique id handler tool
        handler = getToolByName(self, 'portal_uidhandler', None)
        if handler is None:
            return

        # check for remote uid info on object
        uid = getattr(aq_base(self), 'remote_uid', None)
        if uid is None:
            return

        return handler.queryObject(uid, None)

    security.declareProtected(View, 'getRemoteUrl')
    def getRemoteUrl(self):
        """
            returns the remote URL of the Link
        """
        # try getting the remote object by unique id
        remote_url = self._getRemoteUrlTheOldWay()
        remote_obj = self._getObjectByUid()
        if remote_obj:
            url = remote_obj.absolute_url()
            # update the url when changed (avoid unnecessary ZODB writes)
            if url != remote_url:
                self.edit(url)
            return url

        return remote_url

    def _getRemoteUrlTheOldWay(self):
        """Build the url without having taking the uid into account
        """
        portal_url = getToolByName(self, 'portal_url')
        if self.remote_url:
            return portal_url() + '/' + self.remote_url
        else:
            return portal_url()

    security.declareProtected(View, 'getIconURL')
    def getIconURL(self):
        """
        Instead of a static icon, like for Link objects, we want
        to display an icon based on what the Favorite links to.
        """
        try:
            return self.getObject().getIconURL()
        except KeyError:
            utool = getToolByName(self, 'portal_url')
            return '%s/p_/broken' % utool()

    security.declareProtected(View, 'getObject')
    def getObject(self):
        """ Get the actual object that the Favorite is linking to.
        """
        # try getting the remote object by unique id
        remote_obj = self._getObjectByUid()
        if remote_obj is not None:
            return remote_obj

        # XXX: can't use ISiteRoot because absolute_url() depends on REQUEST
        portal_url = getToolByName(self, 'portal_url')
        return portal_url.getPortalObject().restrictedTraverse(self.remote_url)

    security.declarePrivate('_edit')
    def _edit( self, remote_url ):
        """
        Edit the Favorite. Unlike Links, Favorites have URLs that are
        relative to the root of the site.
        """
        # strip off scheme and machine from URL if present
        tokens = urlparse.urlparse( remote_url, 'http' )
        if tokens[1]:
            # There is a nethost, remove it
            t=('', '') + tokens[2:]
            remote_url=urlparse.urlunparse(t)
        # if URL begins with site URL, remove site URL
        portal_url = getToolByName(self, 'portal_url').getPortalPath()
        i = remote_url.find(portal_url)
        if i==0:
            remote_url=remote_url[len(portal_url):]
        # if site is still absolute, make it relative
        if remote_url[:1]=='/':
            remote_url=remote_url[1:]
        self.remote_url=remote_url

        # save unique id of favorite
        self.remote_uid = self._getUidByUrl()

InitializeClass(Favorite)

FavoriteFactory = Factory(Favorite)


@adapter(IFavorite, IObjectAddedEvent)
def handleFavoriteAddedEvent(obj, event):
    """Event subscriber.
    """
    if obj.remote_url:
        obj.edit(obj.remote_url)
