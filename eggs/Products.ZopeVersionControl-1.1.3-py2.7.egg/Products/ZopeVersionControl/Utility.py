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

import os
import time

from AccessControl import getSecurityManager
from App.Common import package_home
from App.class_init import default__class_init__ as InitializeClass
from Persistence import Persistent
from ZODB.TimeStamp import TimeStamp

try:
    from ZODB.serialize import referencesf
except ImportError:  # < Zope 2.8 / ZODB 3.3
    from ZODB.referencesf import referencesf

_dtmldir = os.path.join( package_home( globals() ), 'dtml' )

use_vc_permission = 'Use version control'


def isAVersionableResource(obj):
    """ True if an object is versionable.

    To qualify, the object must be persistent (have its own db record), and
    must not have an true attribute named '__non_versionable__'."""

    if getattr(obj, '__non_versionable__', 0):
        return 0
    return hasattr(obj, '_p_oid')

class VersionInfo(Persistent):
    """A VersionInfo object contains bookkeeping information for version
       controlled objects. The bookkeeping information can be read (but
       not changed) by restricted code."""

    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, history_id, version_id, status):
        self.timestamp = time.time()
        self.history_id = history_id
        self.version_id = version_id
        self.status = status
        self.user_id = _findUserId()

    sticky = None

    CHECKED_OUT = 0
    CHECKED_IN = 1

    def branchName(self):
        if self.sticky is not None and self.sticky[0] == 'B':
            return self.sticky[1]
        return 'mainline'

    def clone(self, clear_sticky=0):
        info = VersionInfo(self.history_id, self.version_id, self.status)
        dict = info.__dict__
        for name, value in self.__dict__.items():
            dict[name] = value
        if clear_sticky:
            if dict.has_key('sticky'):
                del dict['sticky']
        info.user_id = _findUserId()
        info.timestamp = time.time()
        return info

InitializeClass(VersionInfo)



class ReadOnlyJar:
    """A read-only ZODB connection-like object that prevents changes."""

    def __init__(self, base):
        self.__base__ = base

    _invalidating = []

    def __getattr__(self, name):
        return getattr(self.__base__, name)

    def commit(*args, **kw):
        raise VersionControlError(
            'Old versions of objects cannot be modified.'
            )

    def abort(*args, **kw):
        pass



class VersionControlError(Exception):
    pass



def _findUserId():
    user = getSecurityManager().getUser()
    return user.getUserName()

def _findPath(object):
    path = object.getPhysicalPath()
    return '/'.join(path)

def _findModificationTime(object):
    """Find the last modification time for a version-controlled object.
       The modification time reflects the latest modification time of
       the object or any of its persistent subobjects that are not
       themselves version-controlled objects. Note that this will
       return None if the object has no modification time."""

    mtime = getattr(object, '_p_mtime', None)
    if mtime is None:
        return None

    latest = mtime
    conn = object._p_jar
    load = conn._storage.load
    try:
        version = conn._version
    except AttributeError:
        # ZODB 3.9+ compatibility
        version = None
    refs = referencesf

    oids=[object._p_oid]
    done_oids={}
    done=done_oids.has_key
    first = 1

    while oids:
        oid=oids[0]
        del oids[0]
        if done(oid):
            continue
        done_oids[oid]=1
        try: p, serial = load(oid, version)
        except: pass # invalid reference!
        else:
            if first is not None:
                first = None
            else:
                if p.find('U\x0b__vc_info__') == -1:
                    mtime = TimeStamp(serial).timeTime()
                    if mtime > latest:
                        latest = mtime
            refs(p, oids)

    return latest

