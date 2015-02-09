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
"""Form and Widget Interfaces

$Id: interfaces.py 107398 2009-12-30 22:26:34Z faassen $
"""
__docformat__ = 'restructuredtext'

from zope.interface import Interface
from zope.schema import TextLine, Bool
from zope.formlib.interfaces import IWidget, IInputWidget

# BBB: ITerms are also used by z3c.form and possibly other form
# frameworks, so it was moved to zope.browser.interfaces and it's
# preferred to import from there now.
from zope.browser.interfaces import ITerms

from zope.formlib.interfaces import (
    IBrowserWidget, ISimpleInputWidget, ITextBrowserWidget,
    IWidgetInputErrorView, ISourceQueryView)

class IFormCollaborationView(Interface):
    """Views that collaborate to create a single form.

    When a form is applied, the changes in the form need to
    be applied to individual views, which update objects as
    necessary.
    """

    def __call__():
        """Render the view as a part of a larger form.

        Form input elements should be included, prefixed with the
        prefix given to setPrefix.

        `form` and `submit` elements should not be included. They
        will be provided for the larger form.
        """

    def setPrefix(prefix):
        """Set the `prefix` used for names of input elements

        Element names should begin with the given `prefix`,
        followed by a dot.
        """

    def update():
        """Update the form with data from the request."""


class IAddFormCustomization(Interface):
    """API for add form customization.

    Classes supplied when defining add forms may need to override some
    of these methods.

    In particular, when the context of an add form is not an `IAdding`,
    a subclass needs to override `nextURL` and one of `add` or
    `createAndAdd`.

    To see how all this fits together, here's pseudo code for the
    update() method of the form:

    def update(self):
        data = <get data from widgets> # a dict
        self.createAndAdd(data)
        self.request.response.redirect(self.nextURL())

    def createAndAdd(self, data):
        content = <create the content from the data>
        content = self.add(content)
        <set after-add attributes on content>
    """

    def createAndAdd(data):
        """Create a new object from the given data and the resulting object.

        The data argument is a dictionary with values supplied by the form.

        If any user errors occur, they should be collected into a list
        and raised as a ``WidgetsError``.

        (For the default implementation, see pseudo-code in class docs.)
        """

    def add(content):
        """Add the given content.

        This method is overridden when the context of the add form is
        not an `IAdding`.  In this case, the class that customizes the
        form must take over adding the object.

        The default implementation returns `self.context.add(content)`,
        i.e. it delegates to the `IAdding` view.
        """

    def nextURL():
        """Return the URL to be displayed after the add operation.

        This can be relative to the view's context.

        The default implementation returns `self.context.nextURL()`,
        i.e. it delegates to the `IAdding` view.
        """

