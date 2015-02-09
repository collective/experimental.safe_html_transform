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

import logging

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Marshall import Marshaller
from Products.Archetypes.utils import mapply
from Products.Marshall.config import logger
from Products.Marshall.config import TOOL_ID
from Products.Marshall.registry import getComponent
from Products.Marshall.exceptions import MarshallingException
from Acquisition import ImplicitAcquisitionWrapper


def getContext(obj, REQUEST=None):
    context = getattr(obj, 'aq_parent', None)
    if context is not None or REQUEST is None:
        return obj
    return REQUEST['PARENTS'][0]


class ControlledMarshaller(Marshaller):

    def __init__(self, fallback=None, demarshall_hook=None,
                 marshall_hook=None):
        Marshaller.__init__(self, demarshall_hook, marshall_hook)
        self.fallback = fallback

    def delegate(self, method, obj, data=None, file=None, **kw):
        if file is not None:
            kw['file'] = file
        __traceback_info__ = (method, obj, kw)
        context = getContext(obj, kw.get('REQUEST'))
        if context is not obj:
            # If the object is being created by means of a PUT
            # then it has no context, and some of the stuff
            # we are doing here may require a context.
            # Wrapping it in an ImplicitAcquisitionWrapper should
            # be safe as long as nothing tries to persist
            # a reference to the wrapped object.
            obj = ImplicitAcquisitionWrapper(obj, context)
        tool = getToolByName(obj, TOOL_ID, None)
        components = None
        if tool is not None:
            info = kw.copy()
            info['data'] = data
            info['mode'] = method
            components = tool.getMarshallersFor(obj, **info)
        else:
            # Couldn't find a context to get
            # hold of the tool or the tool is not installed.
            logger.log(logging.DEBUG, 'Could not find the marshaller tool. '
                'It might not be installed or you might not '
                'be providing enough context to find it.')
        # We just use the first component, if one is returned.
        if components:
            marshaller = getComponent(components[0])
        else:
            # If no default marshaller was provided then we complain.
            if self.fallback is None:
                raise MarshallingException(
                    "Couldn't get a marshaller for %r, %r" % (obj, kw))
            # Otherwise, use the default marshaller provided. Note it
            # must be an instance, not a factory.
            marshaller = self.fallback
        __traceback_info__ = (marshaller, method, obj, kw)
        args = (obj,)
        if method == 'demarshall':
            args += (data,)
        method = getattr(marshaller, method)
        return mapply(method, *args, **kw)

    def marshall(self, obj, **kw):
        if not 'data' in kw:
            kw['data'] = ''
        return self.delegate('marshall', obj, **kw)

    def demarshall(self, obj, data, **kw):
        if 'file' in kw:
            if not data:
                # XXX Yuck! Shouldn't read the whole file, never.
                # OTOH, if you care about large files, you should be
                # using the PrimaryFieldMarshaller or something
                # similar.
                data = kw['file'].read()
            del kw['file']

        return self.delegate('demarshall', obj, data, **kw)
