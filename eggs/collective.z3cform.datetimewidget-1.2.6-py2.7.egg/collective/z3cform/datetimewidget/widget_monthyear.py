#-*- coding: utf-8 -*- 

#############################################################################
#                                                                           #
#   Copyright (c) 2008 Rok Garbas <rok@garbas.si>                           #
#                                                                           #
# This program is free software; you can redistribute it and/or modify      #
# it under the terms of the GNU General Public License as published by      #
# the Free Software Foundation; either version 3 of the License, or         #
# (at your option) any later version.                                       #
#                                                                           #
# This program is distributed in the hope that it will be useful,           #
# but WITHOUT ANY WARRANTY; without even the implied warranty of            #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
# GNU General Public License for more details.                              #
#                                                                           #
# You should have received a copy of the GNU General Public License         #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                           #
#############################################################################
__docformat__ = "reStructuredText"

import z3c.form
import zope.schema
import zope.interface
import zope.component
from widget_date import DateWidget
from interfaces import IMonthYearWidget


class MonthYearWidget(DateWidget):
    """ Month and year widget """

    zope.interface.implementsOnly(IMonthYearWidget)

    klass = u'monthyear-widget'
    value = ('', '', 1)

@zope.component.adapter(zope.schema.interfaces.IField, z3c.form.interfaces.IFormLayer)
@zope.interface.implementer(z3c.form.interfaces.IFieldWidget)
def MonthYearFieldWidget(field, request):
    """IFieldWidget factory for MonthYearWidget."""
    return z3c.form.widget.FieldWidget(field, MonthYearWidget(request))



