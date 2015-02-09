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


class SequenceWrapper:
    """A helper that manages lazy acquisition wrapping."""
    def __init__(self, parent, items, pairs=None):
        if pairs is not None:
            self.pairs = 1
        self.parent = parent
        self.items = items

    pairs = None

    def __getitem__(self, key):
        item = self.items[key]
        if self.pairs is not None:
            return (item[0], item[1].__of__(self.parent))
        return item.__of__(self.parent)

    def __len__(self):
        return len(self.items)

    def __nonzero__(self):
        return len(self.items) > 0

