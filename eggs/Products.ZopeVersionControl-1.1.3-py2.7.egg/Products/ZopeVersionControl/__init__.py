##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

import ZopeRepository
from App.class_init import default__class_init__ as InitializeClass
from App.ImageFile import ImageFile

def initialize(context):

    context.registerClass(
        instance_class = ZopeRepository.ZopeRepository,
        meta_type      = 'Repository',
        permission     = 'Add Repositories',
        constructors   = ZopeRepository.constructors,
        icon           = 'www/Repository.gif'
      )

    context.registerHelp()
    context.registerHelpTitle('Zope Help')

    registerIcon('VersionHistory.gif')
    registerIcon('Version.gif')


def install_hack():
    # Hackery - don't try this at home, kids. :) This is temporary for
    # testing purposes only.
    from VersionSupport import VersionSupport
    import OFS.SimpleItem, App.Management

    method = App.Management.Tabs.filtered_manage_options
    def filtered_manage_options(self, REQUEST=None, method = method,
                                options = VersionSupport.manage_options):
        result = method(self, REQUEST)
        for item in result:
            if item.get('label') == 'Version Control':
                return result
        for option in options:
            result.append(option)
        return result
    App.Management.Tabs.filtered_manage_options = filtered_manage_options

    for _class in (OFS.SimpleItem.Item, OFS.SimpleItem.Item_w__name__):
        dict = _class.__dict__
        if not hasattr(dict, '__setitem__'):
            # new-style classes don't need this [>=2.8]
            continue

        for name, value in VersionSupport.__dict__.items():
            if name != 'manage_options':
                dict[name] = value

        InitializeClass(_class)


def registerIcon(filename):
    from OFS import misc_
    setattr(misc_.misc_.ZopeVersionControl, filename, 
            ImageFile('www/%s' % filename, globals())
            )
