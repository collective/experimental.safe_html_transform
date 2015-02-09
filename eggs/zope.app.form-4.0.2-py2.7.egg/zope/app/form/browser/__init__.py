##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Browser widgets

$Id: __init__.py 107377 2009-12-30 19:46:00Z faassen $
"""
__docformat__ = 'restructuredtext'

# the implementation of widgets has moved to zope.formlib.widgets
# import directly from there instead.

from zope.formlib.widget import BrowserWidget, DisplayWidget
from zope.formlib.widget import UnicodeDisplayWidget

from zope.formlib.widgets import TextWidget, BytesWidget
from zope.formlib.widgets import TextAreaWidget, BytesAreaWidget
from zope.formlib.widgets import PasswordWidget, FileWidget
from zope.formlib.widgets import ASCIIWidget, ASCIIAreaWidget
from zope.formlib.widgets import IntWidget, FloatWidget
from zope.formlib.widgets import DecimalWidget
from zope.formlib.widgets import DatetimeWidget, DateWidget
from zope.formlib.widgets import DatetimeI18nWidget
from zope.formlib.widgets import DateI18nWidget
from zope.formlib.widgets import DatetimeDisplayWidget
from zope.formlib.widgets import DateDisplayWidget
from zope.formlib.widgets import BytesDisplayWidget
from zope.formlib.widgets import ASCIIDisplayWidget
from zope.formlib.widgets import URIDisplayWidget

# Widgets for boolean fields
from zope.formlib.widgets import CheckBoxWidget
from zope.formlib.widgets import BooleanRadioWidget
from zope.formlib.widgets import BooleanSelectWidget
from zope.formlib.widgets import BooleanDropdownWidget

# Choice and Sequence Display Widgets
from zope.formlib.widgets import ItemDisplayWidget
from zope.formlib.widgets import ItemsMultiDisplayWidget
from zope.formlib.widgets import SetDisplayWidget
from zope.formlib.widgets import ListDisplayWidget

# Widgets for fields with vocabularies.
# Note that these are only dispatchers for the widgets below.
from zope.formlib.widgets import ChoiceDisplayWidget
from zope.formlib.widgets import ChoiceInputWidget
from zope.formlib.widgets import CollectionDisplayWidget
from zope.formlib.widgets import CollectionInputWidget
from zope.formlib.widgets import ChoiceCollectionDisplayWidget
from zope.formlib.widgets import ChoiceCollectionInputWidget

# Widgets that let you choose a single item from a list
# These widgets are multi-views on (field, vocabulary)
from zope.formlib.widgets import SelectWidget
from zope.formlib.widgets import DropdownWidget
from zope.formlib.widgets import RadioWidget

# Widgets that let you choose several items from a list
# These widgets are multi-views on (field, vocabulary)
from zope.formlib.widgets import MultiSelectWidget
from zope.formlib.widgets import MultiSelectSetWidget
from zope.formlib.widgets import MultiSelectFrozenSetWidget
from zope.formlib.widgets import MultiCheckBoxWidget
from zope.formlib.widgets import OrderedMultiSelectWidget

# Widgets that let you enter several items in a sequence
# These widgets are multi-views on (sequence type, value type)
from zope.formlib.widgets import SequenceWidget
from zope.formlib.widgets import TupleSequenceWidget
from zope.formlib.widgets import ListSequenceWidget
from zope.formlib.widgets import SequenceDisplayWidget

from zope.formlib.widgets import ObjectWidget
