# -*- coding: utf-8 -*-
from App.class_init import InitializeClass
from Products.CMFDiffTool.FieldDiff import FieldDiff


class ListDiff(FieldDiff):
    """Text difference"""

    meta_type = "List Diff"

    def _parseField(self, value, filename=None):
        """Parse a field value in preparation for diffing"""
        # Return the list as is for diffing
        return value

InitializeClass(ListDiff)
