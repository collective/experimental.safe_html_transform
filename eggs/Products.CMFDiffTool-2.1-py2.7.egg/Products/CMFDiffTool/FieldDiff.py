# -*- coding: utf-8 -*-
import difflib
from App.class_init import InitializeClass
from Products.CMFDiffTool.BaseDiff import BaseDiff, _getValue

class FieldDiff(BaseDiff):
    """Text difference"""

    meta_type = "Field Diff"

    def _parseField(self, value, filename=None):
        """Parse a field value in preparation for diffing"""
        if filename is None:
            # Since we only want to compare a single field, make a
            # one-item list out of it
            return [value]
        else:
            return [
                self.filenameTitle(filename),
                value
            ]

    def getLineDiffs(self):
        a = self._parseField(self.oldValue, filename=self.oldFilename)
        b = self._parseField(self.newValue, filename=self.newFilename)
        return difflib.SequenceMatcher(None, a, b).get_opcodes()

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

    def ndiff(self):
        """Return a textual diff"""
        r=[]
        a = self._parseField(self.oldValue, filename=self.oldFilename)
        b = self._parseField(self.newValue, filename=self.newFilename)
        for tag, alo, ahi, blo, bhi in self.getLineDiffs():
            if tag == 'replace':
                plain_replace(a, alo, ahi, b, blo, bhi, r)
            elif tag == 'delete':
                dump('-', a, alo, ahi, r)
            elif tag == 'insert':
                dump('+', b, blo, bhi, r)
            elif tag == 'equal':
                dump(' ', a, alo, ahi, r)
            else:
                raise ValueError, 'unknown tag ' + `tag`
        return '\n'.join(r)

InitializeClass(FieldDiff)

def dump(tag, x, lo, hi, r):
    for i in xrange(lo, hi):
        r.append(tag +' ' + str(x[i]))

def plain_replace(a, alo, ahi, b, blo, bhi, r):
    assert alo < ahi and blo < bhi
    # dump the shorter block first -- reduces the burden on short-term
    # memory if the blocks are of very different sizes
    if bhi - blo < ahi - alo:
        dump('+', b, blo, bhi, r)
        dump('-', a, alo, ahi, r)
    else:
        dump('-', a, alo, ahi, r)
        dump('+', b, blo, bhi, r)
