# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004-2008 Enfold Systems, LLC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
$Id$
"""

import pkg_resources

# Kick off Extensions.Install import
from Products.Marshall.Extensions import Install
del Install

# Kick off handler registration
from Products.Marshall import handlers

# Kick off namespace registration
from Products.Marshall import namespaces

from Products.Marshall.marshaller import ControlledMarshaller


def initialize(context):
    from Products.Marshall import registry
    from Products.Marshall import predicates

    context.registerClass(
        registry.Registry,
        permission='Add Marshaller Registry',
        constructors=(registry.manage_addRegistry,),
        icon='www/registry.png',
        )

    context.registerClass(
        instance_class=predicates.Predicate,
        permission='Add Marshaller Predicate',
        constructors=predicates.constructors,
        icon='www/registry.png')

    # Load marshallers registered by the way of egg entry points.
    for ep in pkg_resources.iter_entry_points('marshall.component'):
        component = ep.load()
        registry.registerComponent(
            ep.name, getattr(component, '__name__', ep.name), component)
