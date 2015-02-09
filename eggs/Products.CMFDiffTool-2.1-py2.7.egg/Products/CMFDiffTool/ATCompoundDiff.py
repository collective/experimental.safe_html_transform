# -*- coding: utf-8 -*-
from App.class_init import InitializeClass
from Products.CMFDiffTool.interfaces.portal_diff import IDifference
from Products.CMFDiffTool.TextDiff import TextDiff
from Products.CMFDiffTool.FieldDiff import FieldDiff
from Products.CMFDiffTool.BinaryDiff import BinaryDiff
from Products.CMFDiffTool.ListDiff import ListDiff
from Products.CMFDiffTool.CMFDTHtmlDiff import CMFDTHtmlDiff


AT_FIELD_MAPPING = {'text': 'variable_text',
                    'string': 'variable_text',
                    'datetime': FieldDiff,
                    'file': 'variable_binary',
                    'blob': 'variable_binary',
                    'image': BinaryDiff,
                    'lines': ListDiff,
                    'integer': FieldDiff,
                    'float': FieldDiff,
                    'fixedpoint': FieldDiff,
                    'boolean': FieldDiff,
                    'reference': 'raw:ListDiff'}

AT_EXCLUDED_FIELDS = ('modification_date',)


class ATCompoundDiff:
    """Text difference"""

    meta_type = "Compound Diff for AT types"

    def __init__(self, obj1, obj2, field, id1=None, id2=None):
        if not id1:
            id1 = obj1.getId()
        if not id2:
            id2 = obj2.getId()
        self.id1 = id1
        self.id2 = id2

        fields = self.getFields(obj1, obj2)
        self._diffs = self.generateSubDiffs(fields, obj1, obj2)

    def __getitem__(self, index):
        return self._diffs[index]

    def __len__(self):
        return len(self._diffs)

    def __iter__(self):
        return iter(self._diffs)

    def generateSubDiffs(self, fields, obj1, obj2):
        diff_list = []
        for field in fields:
            klass = field['klass']
            diff = klass(obj1, obj2, field['accessor'], id1=self.id1,
                         id2=self.id2,
                         field_name=field['name'],
                         field_label=field['label'],
                         schemata=field['schemata'])
            diff_list.append(diff)
        return diff_list

    def getFields(self, obj1, obj2):
        fields = []
        # Make sure we get the fields ordered by schemata, as in the edit view
        schematas = obj1.Schemata()
        schemata_names = schematas.keys()

        # Put default first and metadata last
        if 'default' in schemata_names and schemata_names[0] != 'default':
            schemata_names.remove('default')
            schemata_names.insert(0,'default')
        if 'metadata' in schemata_names and schemata_names[-1] != 'metadata':
            schemata_names.remove('metadata')
            schemata_names.insert(-1,'metadata')

        for schemata_name in schemata_names:
            schema = schematas[schemata_name]
            for field in schema.viewableFields(obj1):
                if (AT_FIELD_MAPPING.has_key(field.type) and 
                        field.getName() not in AT_EXCLUDED_FIELDS):
                    is_primary = getattr(field, 'primary' , False)
                    label = field.widget.Label(obj1)
                    diff_type = AT_FIELD_MAPPING[field.type]
                    if IDifference.implementedBy(diff_type):
                        fields.append({'name':field.getName(),
                                    'accessor':field.accessor,
                                    'klass':diff_type,
                                    'primary':is_primary,
                                    'label':label,
                                    'schemata':schemata_name})
                    elif 'raw' in diff_type:
                        #Handle Fields which diff against the edit accessor
                        diff_name = diff_type.split(':')[1]
                        diff_type = globals()[diff_name]
                        fields.append({'name':field.getName(),
                                    'accessor':field.edit_accessor,
                                    'klass':diff_type,
                                    'primary':is_primary,
                                    'label':label,
                                    'schemata':schemata_name})
                    elif diff_type == 'variable_binary':
                        diff_type = BinaryDiff
                        if 'text/' in field.getContentType(obj1) and \
                        'text/' in \
                            obj2.getField(field.getName()).getContentType(obj2):
                            diff_type = TextDiff
                        fields.append({'name':field.getName(),
                                    'accessor':field.accessor,
                                    'klass':diff_type,
                                    'primary':is_primary,
                                    'label':label,
                                    'schemata':schemata_name})
                    elif diff_type == 'variable_text':
                        diff_type = TextDiff
                        if 'html' in field.getContentType(obj1) and \
                        'html' in \
                            obj2.getField(field.getName()).getContentType(obj2):
                            diff_type = CMFDTHtmlDiff
                        fields.append({'name':field.getName(),
                                    'accessor':field.accessor,
                                    'klass':diff_type,
                                    'primary':is_primary,
                                    'label':label,
                                    'schemata':schemata_name})
        return fields

InitializeClass(ATCompoundDiff)
