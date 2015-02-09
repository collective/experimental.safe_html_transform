##################################################################
#
# (C) Copyright 2006 ObjectRealms, LLC
# All Rights Reserved
#
# This file is part of iterate.
#
# iterate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# iterate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iterate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##################################################################
"""
Checkin / Checkout Specific DAV Lock Manipulation and Introspection

$Id: lock.py 1392 2006-06-20 01:02:17Z hazmat $
"""

from plone.locking.interfaces import ILockable

from interfaces import ITERATE_LOCK

__all__ = ['lockContext', 'unlockContext', 'isLocked']

def lockContext( context ):
    lockable = ILockable(context)
    # Be quite forceful - we assume that we won't have gotten here unless
    # we had rights to do this.
    lockable.clear_locks()
    lockable.lock(ITERATE_LOCK, children=True)

def unlockContext( context ):
    lockable = ILockable(context)
    lockable.unlock(ITERATE_LOCK)

def isLocked( context ):
    lockable = ILockable(context)
    lockable.locked()