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
# along with CMFDeployment; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##################################################################

from Products.CMFEditions import Permissions
from Products.CMFCore.permissions import setDefaultRoles

CheckinPermission  = "iterate : Check in content"
CheckoutPermission = "iterate : Check out content"

DEFAULT_ROLES = ('Manager', 'Owner', 'Site Administrator', 'Editor')
setDefaultRoles(CheckinPermission, DEFAULT_ROLES)
setDefaultRoles(CheckoutPermission, DEFAULT_ROLES)
