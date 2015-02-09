##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import MailHost
import SendMailTag


def initialize(context):
    context.registerClass(
        MailHost.MailHost,
        permission='Add MailHost objects',
        constructors=(MailHost.manage_addMailHostForm,
                      MailHost.manage_addMailHost),
        icon='www/MailHost_icon.gif',
    )

    context.registerHelp()
    context.registerHelpTitle('Zope Help')
