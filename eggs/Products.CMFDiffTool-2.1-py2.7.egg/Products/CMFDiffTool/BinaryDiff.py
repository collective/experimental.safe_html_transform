# -*- coding: utf-8 -*-
from os import linesep
from App.class_init import InitializeClass
from Products.CMFDiffTool.BaseDiff import _getValue
from Products.CMFDiffTool.FieldDiff import FieldDiff

class BinaryDiff(FieldDiff):
    """Simple binary difference"""

    meta_type = "Binary Diff"
    inlinediff_fmt = """
<div class="%s">
    <del>%s</del>
    <ins>%s</ins>
</div>
"""

    def _parseField(self, value, filename=None):
        """Parse a field value in preparation for diffing"""
        if filename is None:
            # Since we only want to compare the filename for
            # binary files, return an empty list
            return []
        else:
            return [self.filenameTitle(filename)]

    def testChanges(self, ob):
        """Test the specified object to determine if the change set will apply without errors"""
        value = _getValue(ob, self.field)
        if not self.same and value != self.oldValue:
            raise ValueError, ("Conflict Error during merge", self.field, value, self.oldValue)

    def applyChanges(self, ob):
        """Update the specified object with the difference"""
        # Simplistic update
        self.testChanges(ob)
        if not self.same:
            setattr(ob, self.field, self.newValue)

    def inline_diff(self):
        """Simple inline diff that just checks that the filename
        has changed."""
        css_class = 'FilenameDiff'
        html = []
        if self.oldFilename != self.newFilename:
            html.append(
                self.inlinediff_fmt % (css_class,
                                       self.filenameTitle(self.oldFilename),
                                       self.filenameTitle(self.newFilename))
            )

        if html:
            return linesep.join(html)

InitializeClass(BinaryDiff)

