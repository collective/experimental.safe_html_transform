##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""BBB this module moved to zope.container
"""

# BBB
from zope.container.contained import (
    Contained,
    ObjectMovedEvent,
    ObjectAddedEvent,
    ObjectRemovedEvent,
    ContainerModifiedEvent,
    dispatchToSublocations,
    ContainerSublocations,
    containedEvent,
    contained,
    notifyContainerModified,
    setitem,
    fixing_up,
    uncontained,
    NameChooser,
    DecoratorSpecificationDescriptor,
    DecoratedSecurityCheckerDescriptor,
    ContainedProxyClassProvides,
    ContainedProxy,
)
