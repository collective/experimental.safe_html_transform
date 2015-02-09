# -*- coding: utf-8 -*-
# Copyright (C) 2011 Alterway Solutions 

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING. If not, write to the
# Free Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


import logging
import profilehooks
from zope.interface import Interface
from zope.configuration.fields import GlobalObject, PythonIdentifier
from zope.configuration.exceptions import ConfigurationError
from zope.schema import Int, Bool, Text

logger = logging.getLogger('collective.profiler')

class IProfileDirective(Interface):
    """ZCML directive to apply profiler on fonction
    """

    class_ = GlobalObject(title=u"The class being patched", required=True)
    method = PythonIdentifier(title=u"The method being patched", required=True)
    filename  = Text(title=u"pstats file name",
                             required=False)
    entries = Int(title=u"pstats file name",
                           required=False,
                           default=40)
    skip = Int(title=u"skip the n calls",
               required=False,
               default=0)
    dirs = Bool(title=u"dirs",
                      required=False,
                      default=False)
    sort = Text(title=u"pstats file name",
                required=False,
                )
    immediate = Bool(title=u"Profile immediatly",
                    required=False,
                    default=True)
    
class ITimeCallDirective(Interface):
    """ZCML directive to apply profiler on fonction
    """

    class_ = GlobalObject(title=u"The class being patched", required=True)
    method = PythonIdentifier(title=u"The method being patched", required=True)
    immediate = Bool(title=u"Profile immediatly",
                    required=False,
                    default=True)
    


def profile(_context, class_, method, filename=None, entries=40,
            skip=0, dirs=False,
            sort = None,
            immediate = True):

    """ZCML directive handler"""

    if class_ is None:
        raise ConfigurationError(u"You must specify 'class'")
    if method is None:
        raise ConfigurationError(u"You must specify 'method'")
    old = getattr(class_, method)
    def new(*args, **kwargs):
        return profilehooks.profile(old,
                                    skip = skip,
                                    filename = filename,
                                    immediate = immediate,
                                    dirs = dirs,
                                    sort = sort,
                                    entries = entries,
                                    profiler=('profile',))(*args, **kwargs)
    logger.info('Profile %s of %s' % (method, str(class_)))
    setattr(class_, method, new)
                       
                       
def timecall(_context, class_, method, immediate = True):
    if class_ is None:
        raise ConfigurationError(u"You must specify 'class'")
    if method is None:
        raise ConfigurationError(u"You must specify 'method'")
    old = getattr(class_, method)
    def new(*args, **kwargs):
        return profilehooks.timecall(old,
                                     immediate = immediate)(*args, **kwargs)
    logger.info('Timecall %s of %s' % (method, str(class_)))
    setattr(class_, method, new)
