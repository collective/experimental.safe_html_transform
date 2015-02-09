##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Form utility functions

In Zope 2's formulator, forms provide a basic mechanism for
organizing collections of fields and providing user interfaces for
them, especially editing interfaces.

In Zope 3, formulator's forms are replaced by Schema (See
zope.schema). In addition, the Formulator fields have been replaced by
schema fields and form widgets. Schema fields just express the semantics
of data values. They contain no presentation logic or parameters.
Widgets are views on fields that take care of presentation. The widget
view names represent styles that can be selected by applications to
customise the presentation. There can also be custom widgets with
specific parameters.

This module provides some utility functions that provide some of the
functionality of formulator forms that isn't handled by schema,
fields, or widgets.

$Id: utility.py 107385 2009-12-30 20:25:24Z faassen $
"""
__docformat__ = 'restructuredtext'

from zope import security
from zope.security.proxy import Proxy
from zope.proxy import isProxy
from zope.interface.interfaces import IMethod
from zope.security.interfaces import ForbiddenAttribute, Unauthorized
from zope.formlib.interfaces import WidgetsError, MissingInputError
from zope.formlib.interfaces import InputErrors
from zope.formlib.interfaces import IInputWidget, IDisplayWidget
# BBB
from zope.formlib.utility import (
    setUpWidget,
    setUpWidgets,
    applyWidgetsChanges,
    _fieldlist,
    no_value,
    _widgetHasStickyValue)
    
def setUpEditWidgets(view, schema, source=None, prefix=None,
                     ignoreStickyValues=False, names=None, context=None,
                     degradeInput=False, degradeDisplay=False):
    """Sets up widgets to collect input on a view.

    See `setUpWidgets` for details on `view`, `schema`, `prefix`,
    `ignoreStickyValues`, `names`, and `context`.

    `source`, if specified, is an object from which initial widget values are
    read. If source is not specified, the view context is used as the source.

    `degradeInput` is a flag that changes the behavior when a user does not
    have permission to edit a field in the names.  By default, the function
    raises Unauthorized.  If degradeInput is True, the field is changed to
    an IDisplayWidget.

    `degradeDisplay` is a flag that changes the behavior when a user does not
    have permission to access a field in the names.  By default, the function
    raises Unauthorized.  If degradeDisplay is True, the field is removed from
    the form.

    Returns a list of names, equal to or a subset of the names that were
    supposed to be drawn, with uninitialized undrawn fields missing.
    """
    if context is None:
        context = view.context
    if source is None:
        source = view.context
    security_proxied = isProxy(source, Proxy)
    res_names = []
    for name, field in _fieldlist(names, schema):
        try:
            value = field.get(source)
        except ForbiddenAttribute:
            raise
        except AttributeError:
            value = no_value
        except Unauthorized:
            if degradeDisplay:
                continue
            else:
                raise
        if field.readonly:
            viewType = IDisplayWidget
        else:
            if security_proxied:
                is_accessor = IMethod.providedBy(field)
                if is_accessor:
                    set_name = field.writer.__name__
                    authorized = security.canAccess(source, set_name)
                else:
                    set_name = name
                    authorized = security.canWrite(source, name)
                if not authorized:
                    if degradeInput:
                        viewType = IDisplayWidget
                    else:
                        raise Unauthorized(set_name)
                else:
                    viewType = IInputWidget
            else:
                # if object is not security proxied, might be a standard
                # adapter without a registered checker.  If the feature of
                # paying attention to the users ability to actually set a
                # field is decided to be a must-have for the form machinery,
                # then we ought to change this case to have a deprecation
                # warning.
                viewType = IInputWidget
        setUpWidget(view, name, field, viewType, value, prefix,
                    ignoreStickyValues, context)
        res_names.append(name)
    return res_names

def setUpDisplayWidgets(view, schema, source=None, prefix=None,
                        ignoreStickyValues=False, names=None, context=None,
                        degradeDisplay=False):
    """Sets up widgets to display field values on a view.

    See `setUpWidgets` for details on `view`, `schema`, `prefix`,
    `ignoreStickyValues`, `names`, and `context`.

    `source`, if specified, is an object from which initial widget values are
    read. If source is not specified, the view context is used as the source.

    `degradeDisplay` is a flag that changes the behavior when a user does not
    have permission to access a field in the names.  By default, the function
    raises Unauthorized.  If degradeDisplay is True, the field is removed from
    the form.

    Returns a list of names, equal to or a subset of the names that were
    supposed to be drawn, with uninitialized undrawn fields missing.
    """
    if context is None:
        context = view.context
    if source is None:
        source = view.context
    res_names = []
    for name, field in _fieldlist(names, schema):
        try:
            value = field.get(source)
        except ForbiddenAttribute:
            raise
        except AttributeError:
            value = no_value
        except Unauthorized:
            if degradeDisplay:
                continue
            else:
                raise
        setUpWidget(view, name, field, IDisplayWidget, value, prefix,
                    ignoreStickyValues, context)
        res_names.append(name)
    return res_names

def viewHasInput(view, schema, names=None):
    """Returns ``True`` if the any of the view's widgets contain user input.

    `schema` specifies the set of fields that correspond to the view widgets.

    `names` can be specified to provide a subset of these fields.
    """
    for name, field in _fieldlist(names, schema):
        if  getattr(view, name + '_widget').hasInput():
            return True
    return False

def getWidgetsData(view, schema, names=None):
    """Returns user entered data for a set of `schema` fields.

    The return value is a map of field names to data values.

    `view` is the view containing the widgets. `schema` is the schema that
    defines the widget fields. An optional `names` argument can be provided
    to specify an alternate list of field values to return. If `names` is
    not specified, or is ``None``, `getWidgetsData` will attempt to return
    values for all of the fields in the schema.

    A requested field value may be omitted from the result for one of two
    reasons:

        - The field is read only, in which case its widget will not have
          user input.

        - The field is editable and not required but its widget does not
          contain user input.

    If a field is required and its widget does not have input, `getWidgetsData`
    raises an error.

    A widget may raise a validation error if it cannot return a value that
    satisfies its field's contraints.

    Errors, if any, are collected for all fields and reraised as a single
    `WidgetsError`.
    """
    result = {}
    errors = []

    for name, field in _fieldlist(names, schema):
        widget = getattr(view, name + '_widget')
        if IInputWidget.providedBy(widget):
            if widget.hasInput():
                try:
                    result[name] = widget.getInputValue()
                except InputErrors, error:
                    errors.append(error)
            elif field.required:
                errors.append(MissingInputError(
                    name, widget.label, 'the field is required'))

    if errors:
        raise WidgetsError(errors, widgetsData=result)

    return result

