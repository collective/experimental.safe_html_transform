##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Default implementation of CMFCore. """

def initialize(context):
    from Products.CMFCore.utils import ToolInit
    from Products.CMFCore.utils import ContentInit
    from Products.CMFCore.utils import registerIcon
    from Products.CMFDefault.permissions import AddPortalContent

    import DefaultWorkflow
    import DiscussionTool
    import Document
    import factory
    import Favorite
    import File
    import Image
    import Link
    import MembershipTool
    import MetadataTool
    import NewsItem
    import Portal
    import PropertiesTool
    import RegistrationTool
    import SkinnedFolder
    import SyndicationTool

    # Make sure security is initialized
    import DiscussionItem
    import DublinCore
    import utils

    contentConstructors = ( Document.addDocument
                        , File.addFile
                        , Image.addImage
                        , Link.addLink
                        , Favorite.addFavorite
                        , NewsItem.addNewsItem
                        , SkinnedFolder.addSkinnedFolder
                        )

    tools = ( DiscussionTool.DiscussionTool
            , MembershipTool.MembershipTool
            , RegistrationTool.RegistrationTool
            , PropertiesTool.PropertiesTool
            , MetadataTool.MetadataTool
            , SyndicationTool.SyndicationTool
            )

    # Register the ID to interface data for those items that don't have their 
    # own module
    from Products.CMFCore.utils import registerToolInterface
    from Products.GenericSetup.interfaces import ISetupTool
    registerToolInterface('portal_setup', ISetupTool)
    from Products.MailHost.interfaces import IMailHost
    registerToolInterface('MailHost', IMailHost)

    ToolInit( 'CMF Default Tool'
            , tools=tools
            , icon='tool.gif'
            ).initialize( context )

    # BBB: register oldstyle constructors
    ContentInit( 'CMF Default Content'
               , content_types=()
               , permission=AddPortalContent
               , extra_constructors=contentConstructors
               , visibility=None
               ).initialize( context )

    context.registerClass( Portal.CMFSite
                         , constructors=(factory.addConfiguredSiteForm,
                                         factory.addConfiguredSite)
                         , icon='images/portal.gif'
                         )

    registerIcon( DefaultWorkflow.DefaultWorkflowDefinition
                , 'images/workflow.gif'
                , globals()
                )

    # make registerHelp work with 2 directories
    help = context.getProductHelp()
    lastRegistered = help.lastRegistered
    context.registerHelp(directory='help', clear=1)
    context.registerHelp(directory='interfaces', clear=1)
    if help.lastRegistered != lastRegistered:
        help.lastRegistered = None
        context.registerHelp(directory='help', clear=1)
        help.lastRegistered = None
        context.registerHelp(directory='interfaces', clear=0)
    context.registerHelpTitle('CMF Default Help')
