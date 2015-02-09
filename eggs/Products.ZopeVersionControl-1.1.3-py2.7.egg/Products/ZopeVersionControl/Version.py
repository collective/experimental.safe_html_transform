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

__version__='$Revision: 1.11 $'[11:-2]

import tempfile
import time
from cStringIO import StringIO
from cPickle import Pickler, Unpickler

from Acquisition import Implicit, aq_parent, aq_inner, aq_base
from App.class_init import default__class_init__ as InitializeClass
from Persistence import Persistent
from AccessControl import ClassSecurityInfo
from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem

from Utility import VersionControlError
from nonversioned import listNonVersionedObjects, removeNonVersionedData


def cloneByPickle(obj, ignore_list=()):
    """Makes a copy of a ZODB object, loading ghosts as needed.

    Ignores specified objects along the way, replacing them with None
    in the copy.
    """
    ignore_dict = {}
    for o in ignore_list:
        ignore_dict[id(o)] = o

    def persistent_id(ob, ignore_dict=ignore_dict):
        if ignore_dict.has_key(id(ob)):
            return 'ignored'
        if getattr(ob, '_p_changed', 0) is None:
            ob._p_changed = 0
        return None

    def persistent_load(ref):
        assert ref == 'ignored'
        # Return a placeholder object that will be replaced by
        # removeNonVersionedData().
        placeholder = SimpleItem()
        placeholder.id = "ignored_subobject"
        return placeholder

    stream = StringIO()
    p = Pickler(stream, 1)
    p.persistent_id = persistent_id
    p.dump(obj)
    stream.seek(0)
    u = Unpickler(stream)
    u.persistent_load = persistent_load
    return u.load()


class Version(Implicit, Persistent):
    """A Version is a resource that contains a copy of a particular state
       (content and dead properties) of a version-controlled resource.  A
       version is created by checking in a checked-out resource. The state
       of a version of a version-controlled resource never changes."""

    def __init__(self, version_id, obj):
        self.id = version_id
        self.date_created = time.time()
        self._data = None

    # These attributes are set by the createVersion method of the version
    # history at the time the version is created. The branch is the name
    # of the branch on which the version was created. The prev attribute
    # is the version id of the predecessor to this version. The next attr
    # is a sequence of version ids of the successors to this version.
    branch = 'mainline'
    prev = None
    next = ()

    security = ClassSecurityInfo()

    security.declarePublic('getId')
    def getId(self):
        return self.id

    security.declarePrivate('saveState')
    def saveState(self, obj):
        """Save the state of object as the state for this version of
           a version-controlled resource."""
        self._data = self.stateCopy(obj, self)

    security.declarePrivate('copyState')
    def copyState(self):
        """Return an independent deep copy of the state of the version."""
        data = self.__dict__.get('_data')  # Avoid __of__ hooks
        return self.stateCopy(data, self)

    security.declarePrivate('stateCopy')
    def stateCopy(self, obj, container):
        """Get a deep copy of the state of an object.

        Breaks any database identity references.
        """
        ignore = listNonVersionedObjects(obj)
        res = cloneByPickle(aq_base(obj), ignore)
        removeNonVersionedData(res)
        return res


InitializeClass(Version)
