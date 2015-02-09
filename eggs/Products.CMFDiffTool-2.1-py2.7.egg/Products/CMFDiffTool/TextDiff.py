# -*- coding: utf-8 -*-
import difflib
from os import linesep

from App.class_init import InitializeClass
from zope.component.hooks import getSite

from Products.CMFDiffTool.FieldDiff import FieldDiff
from Products.CMFDiffTool.utils import safe_unicode, safe_utf8
from Products.CMFDiffTool import CMFDiffToolMessageFactory as _


class TextDiff(FieldDiff):
    """Text difference"""

    meta_type = "Lines Diff"
    inlinediff_fmt = """
<div class="%s">
    <del>%s</del>
    <ins>%s</ins>
</div>
"""

    def _parseField(self, value, filename=None):
        """Parse a field value in preparation for diffing"""
        if value is None:
            value = ''
        if filename is None:
            # Split the text into a list for diffs
            return value.splitlines()
        else:
            return [self.filenameTitle(filename)] + value.splitlines()

    def unified_diff(self):
        """Return a unified diff"""
        a = [safe_utf8(i) for i in
             self._parseField(self.oldValue, filename=self.oldFilename)]
        b = [safe_utf8(i) for i in
             self._parseField(self.newValue, filename=self.newFilename)]
        return linesep.join(difflib.unified_diff(a, b, self.id1, self.id2))

    def html_diff(self, context=True, wrapcolumn=40):
        """Return an HTML table showing differences"""
        # difflib is not Unicode-aware, so we need to force everything to
        # utf-8 manually
        a = [safe_unicode(i) for i in
             self._parseField(self.oldValue, filename=self.oldFilename)]
        b = [safe_unicode(i) for i in
             self._parseField(self.newValue, filename=self.newFilename)]
        vis_diff = difflib.HtmlDiff(wrapcolumn=wrapcolumn)
        diff = safe_utf8(vis_diff.make_table(a, b,
                                             safe_unicode(self.id1),
                                             safe_unicode(self.id2),
                                             context=context))
        return diff

    def inline_diff(self):
        """Simple inline diff that just assumes that either the filename
        has changed, or the text has been completely replaced."""
        css_class = 'InlineDiff'
        old_attr = self._parseField(self.oldValue,
                                    filename=self.oldFilename)
        new_attr = self._parseField(self.newValue,
                                    filename=self.newFilename)
        if old_attr:
            old_fname = old_attr.pop(0)
        else:
            old_fname = None
        if new_attr:
            new_fname = new_attr.pop(0)
        else:
            new_fname = None
        a = linesep.join(old_attr or [])
        b = linesep.join(new_attr or [])
        html = []
        if old_fname != new_fname:
            html.append(
                self.inlinediff_fmt % ('%s FilenameDiff' % css_class,
                                       old_fname, new_fname)
            )
        if a != b:
            html.append(
                self.inlinediff_fmt % (css_class, a, b)
            )
        if html:
            return linesep.join(html)

InitializeClass(TextDiff)


class AsTextDiff(TextDiff):
    """
    Specialization of `TextDiff` that converts any value to text in order to
    provide an inline diff visualization. Also translated (i18n) the
    strings `True` and `False`.
    """

    def _parseField(self, value, filename=None):
        if value is None:
            value = ''

        # In tests translation is not available, so we account for this
        # case here.
        translate = getattr(getSite(), 'translate', None)
        if translate is not None:
            value = translate(_(value))

        return TextDiff._parseField(self, str(value), filename)

InitializeClass(AsTextDiff)
