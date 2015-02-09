# -*- coding: utf-8 -*-
## CMFPlacefulWorkflowM
## Copyright (C)2006 Ingeniweb

## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; see the file COPYING. If not, write to the
## Free Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
Zope 3.1-style messagefactory module for Zope <= 2.9 (Zope 3.1)

BBB: Zope 2.8 / Zope X3.0
"""
__version__ = "$Revision: 1.31 $"
# $Source: /cvsroot/ingeniweb/PloneSubscription/SubscriptionTool.py,v $
# $Id: SubscriptionTool.py,v 1.31 2005/10/10 20:43:57 encolpe Exp $
__docformat__ = 'restructuredtext'


from zope.i18nmessageid import MessageIDFactory
msg_factory = MessageIDFactory('cmfplacefulworkflow')

def CMFPlacefulWorkflowMessageFactory(ustr, default=None, mapping=None):
    message = msg_factory(ustr, default)
    if mapping is not None:
        message.mapping.update(mapping)
    return message
