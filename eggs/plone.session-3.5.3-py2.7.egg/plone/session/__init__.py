from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService.PluggableAuthService import \
    registerMultiPlugin
from plone.session.plugins import session


registerMultiPlugin(session.SessionPlugin.meta_type)


def initialize(context):
    context.registerClass(session.SessionPlugin,
            permission = add_user_folders,
            constructors = (session.manage_addSessionPluginForm,
                            session.manage_addSessionPlugin),
            visibility = None)
