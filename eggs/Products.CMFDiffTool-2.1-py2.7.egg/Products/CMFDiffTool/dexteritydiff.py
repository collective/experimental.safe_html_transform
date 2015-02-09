from zope.schema import (Bytes, Iterable, Container, Text, Date, Datetime,
                         Time, Choice, Bool)
from zope.globalrequest import getRequest
from z3c.form.interfaces import INPUT_MODE

from plone.app.textfield import RichText
from plone.autoform.base import AutoFields

from Products.CMFDiffTool.TextDiff import AsTextDiff
from Products.CMFDiffTool.namedfile import NamedFileBinaryDiff
from Products.CMFDiffTool.namedfile import FILE_FIELD_TYPES
from Products.CMFDiffTool.namedfile import NamedFileListDiff
from Products.CMFDiffTool.choicediff import ChoiceDiff
from Products.CMFDiffTool.choicediff import get_schemas
from Products.CMFDiffTool.CMFDTHtmlDiff import CMFDTHtmlDiff
from Products.CMFDiffTool.FieldDiff import FieldDiff
from Products.CMFDiffTool.ListDiff import ListDiff
from Products.CMFDiffTool.TextDiff import TextDiff

# TODO: Perhaps this can be replaced with some kind of Zope 3 style
# adaptation, in order to provide better extensibility.
FIELDS_AND_DIFF_TYPES_RELATION = [
    (FILE_FIELD_TYPES, NamedFileBinaryDiff),
    ((Iterable, Container), ListDiff),
    ((Date, Datetime, Time), AsTextDiff),
    ((Bool,), AsTextDiff),
    ((Choice,), ChoiceDiff),
    ((Text, Bytes), TextDiff),
    ((RichText,), CMFDTHtmlDiff),
]

"""
Relates field types (`zope.schema.Field` subclasses) and "diff types"
(`Products.CMFEditions.BaseDiff.BaseDiff` subclasses).

To find the best diff type for a field type this list will be searched until
a match is found.
If a match is not found then `FALL_BACK_DIFF_TYPE` is used.
"""

FALL_BACK_DIFF_TYPE = FieldDiff

# TODO: Perhaps this is not the best approach. Instead we should write a diff
# type which can handle lists of any kind of elements, providing extensibility
# mechanisms if we want to specialize the handling of certain value types.
# (rafaelbco)
VALUE_TYPES_AND_DIFF_TYPES_RELATION = [
    (FILE_FIELD_TYPES, NamedFileListDiff),
]

"""
When a field is detected to be a list-like field we use this list in the same
fashion as `FIELDS_AND_DIFF_TYPES_RELATION` to try to find the best "diff type
" according to the "value type" of the field, i.e the type of the elements in
the list. If a match is not found then a fall back is used.
"""

# TODO: provide an easier way to exclude fields.
EXCLUDED_FIELDS = ('modification_date', 'changeNote')
"""Names of fields not to compare."""


class DexterityCompoundDiff(object):
    """Same as `Products.CMFDiffTool.ATCompoundDiff.ATCompoundDiff` but for
    Dexterity.
    """

    meta_type = 'Compound Diff for Dexterity types'

    def __init__(self, obj1, obj2, field, id1=None, id2=None):
        self.id1 = id1 or obj1.getId()
        self.id2 = id2 or obj2.getId()
        self._diffs = self._diff(obj1, obj2)

    def __getitem__(self, index):
        return self._diffs[index]

    def __len__(self):
        return len(self._diffs)

    def __iter__(self):
        return iter(self._diffs)

    def _diff(self, obj1, obj2):
        """
        Compute the differences between 2 objects.

        Return: a sequence of `IDifference` objects.
        """
        (default_schema, additional_schemata) = get_schemas(obj1)
        diffs = self._diff_schema(obj1, obj2, default_schema, 'default')

        for schema in additional_schemata:
            diffs.extend(self._diff_schema(obj1, obj2, schema, 'metadata'))

        return diffs

    def _diff_schema(self, obj1, obj2, schema, schema_name):
        """
        Compute the differences between 2 objects in respect to the given
        schema interface.

        Return: a sequence of `IDifference` objects.
        """
        return [
            self._diff_field(obj1, obj2, schema[name], schema_name)
            for name in self._compute_fields_order(schema)
            if name not in EXCLUDED_FIELDS
        ]

    def _diff_field(self, obj1, obj2, field, schema_name):
        """
        Compute the differences between 2 objects in respect to the given
        field (`zope.schema.Field` instance).

        Return: an `IDifference` object.
        """
        diff_type = self._get_diff_type(field)
        return diff_type(
            obj1,
            obj2,
            field.getName(),
            id1=self.id1,
            id2=self.id2,
            field_name=field.getName(),
            field_label=field.title,
            schemata=schema_name
        )

    def _get_diff_type(self, field):
        """
        Return a subclass of `Products.CMFEditions.BaseDiff.BaseDiff` suitable
        for the given `zope.schema.Field` instance.
        """
        diff_type = self._compute_diff_type(
            field, FIELDS_AND_DIFF_TYPES_RELATION)

        if diff_type is ListDiff:
            return (
                self._compute_diff_type(
                    field.value_type, VALUE_TYPES_AND_DIFF_TYPES_RELATION)
                or diff_type
            )

        return diff_type or FALL_BACK_DIFF_TYPE

    def _compute_diff_type(self, field, relation):
        """
        Return the best "diff type" (subclass of
        `Products.CMFEditions.BaseDiff.BaseDiff`) suitable for the given
        `zope.schema.Field` instance according to `relation`. The `relation`
        is searched until a match is found. Return `None` otherwise.

        Parameters:
        field -- `zope.schema.Field` instance.
        relation -- Sequence of tuples (field_types, diff_type) where
            field_types is a tuple of `zope.schema.Field` subclasses
            and diff_type is a `Products.CMFEditions.BaseDiff.BaseDiff`
            subclass.
        """

        for (field_types, diff_type) in relation:
            if isinstance(field, field_types):
                return diff_type

        return None

    def _compute_fields_order(self, schema):
        """
        Given a `schema` interface compute the field ordering the way
        `plone.autoform` does, i.e taking into account `plone.directives.form`
        ordering directives.

        Return: a list of field names in order.
        """
        auto_fields = AutoFields()
        auto_fields.schema = schema
        auto_fields.request = getRequest()
        auto_fields.mode = INPUT_MODE
        auto_fields.updateFieldsFromSchemata()
        return auto_fields.fields
