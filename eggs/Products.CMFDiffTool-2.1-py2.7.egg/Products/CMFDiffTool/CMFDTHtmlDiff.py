# -*- coding: utf-8 -*-
from App.class_init import InitializeClass
from Products.CMFDiffTool.TextDiff import TextDiff
from Products.CMFDiffTool.libs import htmldiff

# Give it a dumb name so it doesn't conflict with all the other html diffs
# around.  This uses Ian Bicking's very nice htmldiff.py from Web Ware for
# Python.
class CMFDTHtmlDiff(TextDiff):
    """Text difference"""

    meta_type = "HTML Diff"

    def inline_diff(self):
        """Return a specialized diff for HTML"""
        a = '\n'.join(self._parseField(self.oldValue,
                                       filename=self.oldFilename))
        b = '\n'.join(self._parseField(self.newValue,
                                       filename=self.newFilename))
        return htmldiff.htmldiff(a, b)

    def _parseField(self, value, filename=None):
        """Use the field's raw value if available."""
        if value is None:
            value = ''
        else:
            value = getattr(value, 'raw', value)
        return TextDiff._parseField(self, value, filename)

InitializeClass(CMFDTHtmlDiff)
