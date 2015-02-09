from zope.component import getUtility
from App.class_init import InitializeClass

from Products.CMFDiffTool.TextDiff import AsTextDiff

from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import getAdditionalSchemata


def title_or_value(vocabulary, value):
    """
    Given a `vocabulary` and a `value` in that vocabulary, return the
    corresponding title or `value` if there is no title.
    """
    try:
        return vocabulary.getTerm(value).title or value
    except LookupError:
        # can happen in some cases, e.g. when using
        # zope.schema.vocabulary.TreeVocabulary
        # XXX: There might be a better solution than just returning the value
        return value


def get_schemas(obj):
    """Return a tuple (schema, additional_schemata)."""
    fti = getUtility(IDexterityFTI, name=obj.portal_type)
    schema = fti.lookupSchema()
    additional_schemata = getAdditionalSchemata(context=obj)
    return (schema, additional_schemata)


def get_field_object(obj, field_name):
    """
    Return the `zope.schema.Field` object corresponding to `field_name` in
    `obj`. Return `None` if not found.
    """
    (schema, additional_schemata) = get_schemas(obj)
    schemas = [schema] + list(additional_schemata)
    for s in schemas:
        field = s.get(field_name, None)
        if field is not None:
            return field
    return None


class ChoiceDiff(AsTextDiff):
    """
    Diff for choice fields.

    It's implemented as an specialization of `AsTextDiff`. The difference is
    that this class tries to obtain the title corresponding to the value from
    the vocabulary associated with the field in order to provide an
    user-friendlier inline diff to the user.
    """
    def __init__(self, obj1, obj2, field, id1=None, id2=None, field_name=None,
                 field_label=None, schemata=None):
        AsTextDiff.__init__(self, obj1, obj2, field, id1, id2, field_name,
                            field_label, schemata)
        self._vocabulary = None

        # Tries to find a vocabulary. First we need to find an object and
        # the field instance.
        obj = obj1 if (obj1 is not None) else obj2
        field_name = field_name or field
        field_instance = (
            get_field_object(obj, field_name) if (obj and field_name)
            else None
        )

        if field_instance is not None:
            # Binding the field to an object will construct the vocabulary
            # using a factory if necessary.
            self._vocabulary = field_instance.bind(obj).vocabulary

    def _parseField(self, value, filename=None):
        if value is None:
            value = ''
        elif self._vocabulary is not None:
            value = title_or_value(self._vocabulary, value)

        return AsTextDiff._parseField(self, value, filename)

InitializeClass(ChoiceDiff)
