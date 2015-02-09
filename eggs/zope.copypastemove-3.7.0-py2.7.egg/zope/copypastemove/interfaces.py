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
"""Copy and Move support
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface, implements

class IObjectMover(Interface):
    """Use `IObjectMover(obj)` to move an object somewhere."""

    def moveTo(target, new_name=None):
        """Move this object to the target given.

        Returns the new name within the target.
        """

    def moveable():
        """Returns ``True`` if the object is moveable, otherwise ``False``."""

    def moveableTo(target, name=None):
        """Say whether the object can be moved to the given `target`.

        Returns ``True`` if it can be moved there. Otherwise, returns
        ``False``.
        """

class IObjectCopier(Interface):

    def copyTo(target, new_name=None):
        """Copy this object to the `target` given.

        Returns the new name within the `target`. After the copy
        is created and before adding it to the target container,
        an `IObjectCopied` event is published.
        """

    def copyable():
        """Returns ``True`` if the object is copyable, otherwise ``False``."""

    def copyableTo(target, name=None):
        """Say whether the object can be copied to the given `target`.

        Returns ``True`` if it can be copied there. Otherwise, returns
        ``False``.
        """

class IContainerItemRenamer(Interface):

    def renameItem(oldName, newName):
        """Renames an object in the container from oldName to newName.

        Raises ItemNotFoundError if oldName doesn't exist in the container.

        Raises DuplicationError if newName is already used in the container.
        """

class IPrincipalClipboard(Interface):
    """Interface for adapters that store/retrieve clipboard information
    for a principal.

    Clipboard information consists of mappings of
      ``{'action':action, 'target':target}``.
    """

    def clearContents():
        """Clear the contents of the clipboard"""

    def addItems(action, targets):
        """Add new items to the clipboard"""

    def setContents(clipboard):
        """Replace the contents of the clipboard by the given value"""

    def getContents():
        """Return the contents of the clipboard"""

class IItemNotFoundError(Interface):
    pass

class ItemNotFoundError(LookupError):
    implements(IItemNotFoundError)
