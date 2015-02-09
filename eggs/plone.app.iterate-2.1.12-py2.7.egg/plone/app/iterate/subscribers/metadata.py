##################################################################
#
# (C) Copyright 2006-2007 ObjectRealms, LLC
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
# along with CMFDeployment; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##################################################################
"""
$Id: metadata.py 1824 2007-02-08 17:59:41Z hazmat $
"""

from AccessControl import getSecurityManager
from DateTime import DateTime
from plone.app.iterate.util import get_storage
from plone.app.iterate.interfaces import keys

def handleCheckout( event ):
    # no cleanup since we annotate the relation and rely on its lifecycle.
    storage = get_storage( event.relation )
    user = getSecurityManager().getUser()
    storage[keys.checkout_user] = user.getId()
    storage[keys.checkout_time] = DateTime()

