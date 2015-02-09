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
$Id: interfaces.py 96280 2009-02-08 22:27:11Z nadako $
"""
import zope.interface

class ResumeCopy(Exception):
    """Don't use the hook, resume the copy.
    
    This is a special exception, raised from the copy hook to signal
    copier that it should continue copying the object recursively.
    
    See ICopyHook.__call__ method documentation.
    """

class ICopyHook(zope.interface.Interface):
    """An adapter to an object that is being copied"""
    
    def __call__(toplevel, register):
        """Given the top-level object that is being copied, return the
        version of the adapted object that should be used in the new copy.

        Raising ResumeCopy means that you are foregoing the hook: the
        adapted object will continue to be recursively copied as usual.

        If you need to have a post-copy actions executed, register a
        callable with ``register``.  This callable must take a single
        argument: a callable that, given an object from the original,
        returns the equivalent in the copy.
        
        See README.txt for more explanation.
        """
