##############################################################################
#
# Copyright (c) 2001-2004 Zope Corporation and Contributors. 
# Copyright (c) 2004 Christian Heimes and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL). A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""MailHost Product Initialization
$Id: 
"""
import SecureMailHost
import mail

def initialize(context):
    context.registerClass(
        SecureMailHost.SecureMailHost,
        permission='Add secure MailHost objects',
        constructors=(SecureMailHost.manage_addMailHostForm,
                      SecureMailHost.manage_addMailHost),
        icon='www/MailHost_icon.gif',
    )
