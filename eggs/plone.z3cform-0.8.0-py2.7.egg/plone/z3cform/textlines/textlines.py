##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
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
"""
$Id: __init__.py 97 2007-03-29 22:58:27Z rineichen $
"""
__docformat__ = "reStructuredText"

import zope.component
import zope.interface
import zope.schema.interfaces

try:

    # z3c.form 2.0 or later

    from z3c.form.interfaces import ITextLinesWidget
    from z3c.form.browser.textlines import TextLinesWidget
    from z3c.form.browser.textlines import TextLinesFieldWidget
    from z3c.form.browser.textlines import TextLinesFieldWidgetFactory
    from z3c.form.converter import TextLinesConverter

except ImportError:

    # backport for z3c.form 1.9


    from z3c.form import interfaces
    from z3c.form import widget
    from z3c.form import converter
    from z3c.form.browser import textarea

    class ITextLinesWidget(interfaces.IWidget):
        """Text lines widget."""

    class TextLinesWidget(textarea.TextAreaWidget):
        """Input type sequence widget implementation."""
        zope.interface.implementsOnly(ITextLinesWidget)


    def TextLinesFieldWidget(field, request):
        """IFieldWidget factory for TextLinesWidget."""
        return widget.FieldWidget(field, TextLinesWidget(request))


    @zope.interface.implementer(interfaces.IFieldWidget)
    def TextLinesFieldWidgetFactory(field, value_type, request):
        """IFieldWidget factory for TextLinesWidget."""
        return TextLinesFieldWidget(field, request)

    class TextLinesConverter(converter.BaseDataConverter):
        """Data converter for ITextLinesWidget."""

        zope.component.adapts(
            zope.schema.interfaces.ISequence, ITextLinesWidget)

        def toWidgetValue(self, value):
            """Convert from text lines to HTML representation."""
            # if the value is the missing value, then an empty list is produced.
            if value is self.field.missing_value:
                return u''
            return u'\n'.join(unicode(v) for v in value)

        def toFieldValue(self, value):
            """See interfaces.IDataConverter"""
            widget = self.widget
            collectionType = self.field._type
            if isinstance(collectionType, tuple):
                collectionType = collectionType[-1]
            if not len(value):
                return self.field.missing_value
            valueType = self.field.value_type._type
            if isinstance(valueType, tuple):
                valueType = valueType[0]
            return collectionType(valueType(v) for v in value.split())

# additional

class TextLinesSetConverter(TextLinesConverter):
    """Data converter for ITextLinesWidget operating on a set."""

    zope.component.adapts(
        zope.schema.interfaces.ISet, ITextLinesWidget)

    def toWidgetValue(self, value):
        """Convert from text lines to HTML representation."""
        # if the value is the missing value, then an empty list is produced.
        if value is self.field.missing_value:
            return u''
        return u'\n'.join(unicode(v) for v in sorted(value))

class TextLinesFrozenSetConverter(TextLinesConverter):
    """Data converter for ITextLinesWidget operating on a frozenset."""

    zope.component.adapts(
        zope.schema.interfaces.IFrozenSet, ITextLinesWidget)

    def toWidgetValue(self, value):
        """Convert from text lines to HTML representation."""
        # if the value is the missing value, then an empty list is produced.
        if value is self.field.missing_value:
            return u''
        return u'\n'.join(unicode(v) for v in sorted(value))
