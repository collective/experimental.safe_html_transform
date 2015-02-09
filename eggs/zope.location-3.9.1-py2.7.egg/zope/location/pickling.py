##############################################################################
#
# Copyright (c) 2003-2009 Zope Foundation and Contributors.
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
"""Location copying/pickling support
"""
__docformat__ = 'restructuredtext'

from zope.component import adapts
from zope.interface import implements
from zope.location.interfaces import ILocation
from zope.location.location import inside

try:
    from zope.copy.interfaces import ICopyHook, ResumeCopy
except ImportError:
    raise NotImplementedError("zope.location.pickling is not supported "
        "because zope.copy is not available")


class LocationCopyHook(object):
    """Copy hook to preserve copying referenced objects that are not
    located inside object that's being copied.
    """
    
    adapts(ILocation)
    implements(ICopyHook)
    
    def __init__(self, context):
        self.context = context
    
    def __call__(self, toplevel, register):
        if not inside(self.context, toplevel):
            return self.context
        raise ResumeCopy

# BBB 2009-09-02
# The locationCopy was replaced by more generic "clone" function
# in the zope.copy package. This reference may be removed someday.
from zope.copy import clone as locationCopy

# BBB 2009-09-02
# The CopyPersistent was made more generic and moved to the
# zope.copy package. This reference may be removed someday.
from zope.copy import CopyPersistent
