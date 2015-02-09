# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004-2006 Enfold Systems, LLC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
$Id$
"""

from zope.interface import implements

from OFS.SimpleItem import SimpleItem
from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import view, manage_properties
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.Marshall.expression import Expression, createExprContext
from Products.Marshall.registry import createPredicate, registerPredicate
from Products.Marshall.registry import getRegisteredPredicates
from Products.Marshall.registry import getRegisteredComponents
from Products.Marshall.interfaces import IPredicate


class Predicate(SimpleItem):
    """ A Predicate for selecting marshallers.

    Each Predicate is composed of a Expression  which
    is evaluated in the context of the object to
    decide if the Predicate applies, and returns
    a component name to be used for that object.
    """

    implements(IPredicate)

    meta_type = "Marshaller Predicate"
    predicate_type = None
    predicate_name = None
    security = ClassSecurityInfo()

    manage_options = (
        {'label': 'Edit', 'action': 'manage_changePredicateForm'},
        ) + SimpleItem.manage_options

    security.declareProtected('View management screens',
      'manage_changePredicateForm', 'manage_main', 'manage')

    manage_changePredicateForm = PageTemplateFile(
        '../www/predicateChange', globals(),
        __name__='manage_changePredicateForm')

    manage_changePredicateForm._owner = None
    manage = manage_main = manage_changePredicateForm

    def __init__(self, id, title, expression='', component_name=''):
        self.id = id
        self.title = title
        self.setExpression(expression)
        self.setComponentName(component_name)

    security.declareProtected(view, 'getPredicateType')
    def getPredicateType(self):
        return self.predicate_type

    security.declareProtected(view, 'getPredicateName')
    def getPredicateName(self):
        return self.predicate_name

    security.declareProtected(view, 'apply')
    def apply(self, obj, **kw):
        """ Evaluate expression using the object as
        context and return a component name if applicable.
        """
        if not self.getExpression():
            # Short-circuit for speedup when no expression.
            return (self.getComponentName(),)
        context = createExprContext(obj, **kw)
        if self.expression(context):
            return (self.getComponentName(),)
        return ()

    security.declareProtected(view, 'getComponentName')
    def getComponentName(self):
        """ Return the component name configured for
        this predicate.
        """
        return self._component_name

    security.declareProtected(manage_properties, 'setComponentName')
    def setComponentName(self, component_name):
        """ Change the component name """
        valid_components = [i['name'] for i in getRegisteredComponents()]
        if component_name not in valid_components:
            raise ValueError('Not a valid registered '
                             'component: %s' % component_name)
        self._component_name = component_name

    security.declareProtected(manage_properties, 'setExpression')
    def setExpression(self, expression):
        """ Change the expression """
        self._expression_text = expression
        self._expression = Expression(expression)

    security.declareProtected(view, 'expression')
    def expression(self, context):
        """ Evaluate the expression using context """
        return self._expression(context)

    security.declareProtected(view, 'getExpression')
    def getExpression(self):
        """ Get the expression as text """
        return self._expression_text

    def manage_availableComponents(self):
        return getRegisteredComponents()

    security.declareProtected(manage_properties, 'manage_changePredicate')
    def manage_changePredicate(self, title=None,
                               expression=None,
                               component_name=None,
                               REQUEST=None):
        """ Change the settings of this predicate """

        if title is not None:
            self.title = title
        if expression is not None:
            self.setExpression(expression)
        if component_name is not None:
            self.setComponentName(component_name)

        if REQUEST is not None:
            message = 'Predicate Constraints Changed.'
            return self.manage_changePredicateForm(
                manage_tabs_message=message,
                management_view='Edit')
        return self

InitializeClass(Predicate)
registerPredicate('default', 'Default Predicate', Predicate)


def manage_addPredicate(self, id, title, predicate, expression,
                        component_name, REQUEST=None):
    """ Factory method that creates a Property Set Predicate"""
    obj = createPredicate(predicate, id, title, expression, component_name)
    self._setObject(id, obj)

    if REQUEST is not None:
        next = 'manage_main'
        if hasattr(obj, 'manage_changeSettingsForm'):
            next = 'manage_changeSettingsForm'
        REQUEST['RESPONSE'].redirect('/'.join((self.absolute_url(), id, next)))

    return self._getOb(id)


def manage_availablePredicates(self):
    return getRegisteredPredicates()


def manage_availableComponents(self):
    return getRegisteredComponents()

manage_addPredicateForm = PageTemplateFile(
    '../www/predicateAdd', globals(),
    __name__='manage_addPredicateForm')

constructors = (
  ('manage_addPredicateForm', manage_addPredicateForm),
  ('manage_addPredicate', manage_addPredicate),
  ('manage_availablePredicates', manage_availablePredicates),
  ('manage_availableComponents', manage_availableComponents),
)
