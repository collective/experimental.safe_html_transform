# -*- coding: utf-8 -*-
"""CMFDiffTool.py

   Calculate differences between content objects
"""

from zope.i18n import translate
from zope.interface import implements

import Acquisition
from Acquisition import aq_base
from App.class_init import InitializeClass
from Products.CMFDiffTool.interfaces import IDifference
from Products.CMFDiffTool import CMFDiffToolMessageFactory as _

class BaseDiff:
    """Basic diff type"""

    implements(IDifference)
    __allow_access_to_unprotected_subobjects__ = 1
    meta_type = "Base Diff"

    def __init__(self, obj1, obj2, field, id1=None, id2=None,
                 field_name=None, field_label=None,schemata=None):
        self.field = field
        self.oldValue = _getValue(obj1, field, field_name)
        self.newValue = _getValue(obj2, field, field_name)
        self.same = (self.oldValue == self.newValue)
        if not id1 and hasattr(obj1, 'getId'):
            id1 = obj1.getId()
        if not id2 and hasattr(obj2, 'getId'):
            id2 = obj2.getId()
        self.id1 = id1
        self.id2 = id2
        self.label = field_label or field
        self.schemata = schemata or 'default'
        fld1 = _getValue(obj1, field, field_name, convert_to_str=False)
        fld2 = _getValue(obj2, field, field_name, convert_to_str=False)
        if hasattr(fld1, 'getFilename'):
            self.oldFilename = fld1.getFilename()
        else:
            self.oldFilename = None
        if hasattr(fld2, 'getFilename'):
            self.newFilename = fld2.getFilename()
        else:
            self.newFilename = None
        if self.oldFilename is not None and self.newFilename is not None \
           and self.same:
            self.same = (self.oldFilename == self.newFilename)

    def testChanges(self, ob):
        """Test the specified object to determine if the change set
        will apply without errors"""
        pass

    def applyChanges(self, ob):
        """Update the specified object with the difference"""
        pass

    def filenameTitle(self, filename):
        """Translate the filename leading text
        """
        msg = _(u"Filename: ${filename}",
                mapping={'filename': filename})
        return translate(msg)


def _getValue(ob, field, field_name, convert_to_str=True):
    # Check for the attribute without acquisition.  If it's there,
    # grab it *with* acquisition, so things like ComputedAttribute
    # will work
    if field and hasattr(aq_base(ob), field):
        value = getattr(ob, field)
    elif hasattr(aq_base(ob), 'getField'):
        # Archetypes with an adapter extended schema needs special handling
        field = ob.getField(field_name)
        if field is None:
            raise AttributeError, field
        value = field.getAccessor(ob)
    else:
        raise AttributeError, field

    # Handle case where the field is a method
    try:
        value = value()
    except (AttributeError, TypeError):
        pass

    if convert_to_str:
        # If this is some object, convert it to a string
        try:
            if isinstance(value, Acquisition.Implicit):
                value = str(value)
        except TypeError:
            pass

    return value

InitializeClass(BaseDiff)
