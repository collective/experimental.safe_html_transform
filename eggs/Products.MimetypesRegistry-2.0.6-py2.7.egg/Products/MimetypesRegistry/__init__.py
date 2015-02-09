from Products.MimetypesRegistry import MimeTypesRegistry
from AccessControl.SecurityInfo import allow_module, allow_class

GLOBALS = globals()
PKG_NAME = 'MimetypesRegistry'

tools = (
    MimeTypesRegistry.MimeTypesRegistry,
    )

from Products.MimetypesRegistry import mime_types
from Products.MimetypesRegistry.common import MimeTypeException

allow_module('Products.MimetypesRegistry.common')
allow_class(MimeTypeException)

def initialize(context):
    from Products.CMFCore import utils
    utils.ToolInit("%s Tool" % PKG_NAME,
                   tools=tools,
                   icon="tool.gif",
                   ).initialize(context)
