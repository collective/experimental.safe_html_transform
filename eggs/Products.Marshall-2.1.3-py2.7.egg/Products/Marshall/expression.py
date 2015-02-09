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
Persistent TALES Expression. Highly inspired (read copied)
from CMFCore's Expression.

$Id$
"""

from Persistence import Persistent
from App.class_init import InitializeClass
from Acquisition import aq_inner, aq_parent
from AccessControl import getSecurityManager, ClassSecurityInfo

from Products.PageTemplates.Expressions import getEngine
from Products.PageTemplates.Expressions import SecureModuleImporter


class Expression(Persistent):
    """A Persistent TALES Expression"""

    _text = ''
    _v_compiled = None

    security = ClassSecurityInfo()

    def __init__(self, text):
        self._text = text
        self._v_compiled = getEngine().compile(text)

    def __call__(self, econtext):
        compiled = self._v_compiled
        if compiled is None:
            compiled = self._v_compiled = getEngine().compile(self._text)
        res = compiled(econtext)
        if isinstance(res, Exception):
            raise res
        return res

InitializeClass(Expression)


def createExprContext(obj, **kw):
    """ Provides names for TALES expressions.
    """
    if obj is None:
        object_url = ''
    else:
        object_url = obj.absolute_url()

    user = getSecurityManager().getUser()

    data = {
        'object_url':   object_url,
        'object':       obj,
        'nothing':      None,
        'request':      getattr(obj, 'REQUEST', None),
        'modules':      SecureModuleImporter,
        'user':         user,
        }
    if 'mimetype' in kw and not 'content_type' in kw:
        # Alias content_type to mimetype
        kw['content_type'] = kw['mimetype']
    data.update(kw)
    for k in ('filename', 'content_type', 'data', 'mimetype'):
        data.setdefault(k, None)
    return getEngine().getContext(data)
