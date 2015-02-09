##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id: __init__.py 96250 2009-02-08 16:15:43Z nadako $
"""
import tempfile
import cPickle

from zope.copy import interfaces

def clone(obj):
    """Clone an object by pickling and unpickling it"""
    tmp = tempfile.TemporaryFile()
    persistent = CopyPersistent(obj)

    # Pickle the object to a temporary file
    pickler = cPickle.Pickler(tmp, 2)
    pickler.persistent_id = persistent.id
    pickler.dump(obj)

    # Now load it back
    tmp.seek(0)
    unpickler = cPickle.Unpickler(tmp)
    unpickler.persistent_load = persistent.load

    res = unpickler.load()
    # run the registered cleanups
    def convert(obj):
        return unpickler.memo[pickler.memo[id(obj)][0]]
    for call in persistent.registered:
        call(convert)
    return res

def copy(obj):
    """Clone an object, clearing the __name__ and __parent__ attribute
    values of the copy."""
    res = clone(obj)
    if getattr(res, '__parent__', None) is not None:
        try:
            res.__parent__ = None
        except AttributeError:
            pass
    if getattr(res, '__name__', None) is not None:
        try:
            res.__name__ = None
        except AttributeError:
            pass
    return res

class CopyPersistent(object):
    """A helper class providing the persisntent_id and persistent_load
    functions for pickling and unpickling respectively.
    
    It uses the adaptation to ICopyHook to allow control over object
    copying. See README.txt for more information on that mechanism.
    """

    def __init__(self, obj):
        self.toplevel = obj
        self.pids_by_id = {}
        self.others_by_pid = {}
        self.load = self.others_by_pid.get
        self.registered = []

    def id(self, obj):
        hook = interfaces.ICopyHook(obj, None)
        if hook is not None:
            oid = id(obj)
            if oid in self.pids_by_id:
                return self.pids_by_id[oid]
            try:
                res = hook(self.toplevel, self.registered.append)
            except interfaces.ResumeCopy:
                pass
            else:
                pid = len(self.others_by_pid)
    
                # The following is needed to overcome a bug
                # in pickle.py. The pickle checks the boolean value
                # of the id, rather than whether it is None.
                pid += 1
    
                self.pids_by_id[oid] = pid
                self.others_by_pid[pid] = res
                return pid
        return None
