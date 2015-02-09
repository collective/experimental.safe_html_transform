from App.class_init import InitializeClass

from plone.namedfile import NamedFile

from Products.CMFDiffTool.BinaryDiff import BinaryDiff
from Products.CMFDiffTool.ListDiff import ListDiff
from Products.CMFDiffTool.TextDiff import TextDiff

FILE_FIELD_TYPES = []

try:
    from plone.namedfile import field
    FILE_FIELD_TYPES.extend([field.NamedFile, field.NamedImage])

    if getattr(field, 'HAVE_BLOBS', True):
        FILE_FIELD_TYPES.extend([field.NamedBlobFile, field.NamedBlobImage])
except ImportError:
    pass

FILE_FIELD_TYPES = tuple(FILE_FIELD_TYPES)


def named_file_as_str(f):
    return '' if f is None else '%s (%d bytes)' % (f.filename, len(f.data))


def is_same(old_data, old_filename, new_data, new_filename):
    if old_data != new_data:
        return False

    if (old_filename is not None) and (new_filename is not None):
        return old_filename == new_filename

    return True


class NamedFileBinaryDiff(BinaryDiff):

    def __init__(self, obj1, obj2, field, id1=None, id2=None, field_name=None,
                 field_label=None, schemata=None):

        self.field = field
        self.label = field_label or field
        self.schemata = schemata or 'default'
        self.field_name = field_name or field

        old_field = getattr(obj1, field)
        new_field = getattr(obj2, field)

        self.oldValue = getattr(old_field, 'data', None)
        self.newValue = getattr(new_field, 'data', None)

        self.id1 = id1 or getattr(obj1, 'getId', lambda: None)()
        self.id2 = id2 or getattr(obj2, 'getId', lambda: None)()

        self.oldFilename = getattr(old_field, 'filename', None)
        self.newFilename = getattr(new_field, 'filename', None)

        self.same = is_same(
            self.oldValue, self.oldFilename, self.newValue, self.newFilename)

    def _parseField(self, value, filename=None):
        return [
            '' if (value is None)
            else named_file_as_str(NamedFile(data=value, filename=filename))
        ]

    def inline_diff(self):
        css_class = 'InlineDiff'
        old = self._parseField(self.oldValue, self.oldFilename)[0]
        new = self._parseField(self.newValue, self.newFilename)[0]

        return '' if self.same else self.inlinediff_fmt % (css_class, old, new)

InitializeClass(NamedFileBinaryDiff)


def make_lists_same_length(s1, s2, dummy_element):
    if len(s1) > len(s2):
        s2 += [dummy_element] * (len(s1) - len(s2))
    if len(s2) > len(s1):
        s1 += [dummy_element] * (len(s2) - len(s1))


class NamedFileListDiff(ListDiff):
    """Specialization of `ListDiff` to handle lists of files better."""

    same_fmt = """<div class="%s">%s</div>"""
    inlinediff_fmt = TextDiff.inlinediff_fmt

    def __init__(self, obj1, obj2, field, id1=None, id2=None, field_name=None,
                 field_label=None, schemata=None):
        ListDiff.__init__(self, obj1, obj2, field, id1, id2, field_name,
                          field_label, schemata)
        old_values = list(self.oldValue or [])
        new_values = list(self.newValue or [])

        self.same = True
        if len(old_values) != len(new_values):
            self.same = False
        else:
            for (old, new) in zip(old_values, new_values):
                if not is_same(old.data, old.filename, new.data, new.filename):
                    self.same = False
                    break

    def _parseField(self, value, filename=None):
        value = value or []
        return [named_file_as_str(f) for f in value]

    def inline_diff(self):
        if self.same:
            return None

        css_class = 'InlineDiff'

        old_reprs = self._parseField(self.oldValue, None)
        new_reprs = self._parseField(self.newValue, None)

        old_data = [
            {'repr': repr, 'data': value.data, 'filename': value.filename}
            for (repr, value) in zip(old_reprs, self.oldValue or [])
        ]
        new_data = [
            {'repr': repr, 'data': value.data, 'filename': value.filename}
            for (repr, value) in zip(new_reprs, self.newValue or [])
        ]

        dummy_dict = {'repr': '', 'data': None, 'filename': None}
        make_lists_same_length(old_data, new_data, dummy_dict)

        is_same_dict = lambda d1, d2: is_same(
            d1['data'], d1['filename'], d2['data'], d2['filename']
        )

        return '\n'.join([
            ((self.same_fmt % (css_class, d_old['repr']))
             if is_same_dict(d_old, d_new) else self.inlinediff_fmt
             % (css_class, d_old['repr'], d_new['repr'])
             ) for (d_old, d_new) in zip(old_data, new_data)])

InitializeClass(NamedFileListDiff)
