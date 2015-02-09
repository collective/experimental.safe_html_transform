from Products.CMFCore.utils import ToolInit
from Products.PloneLanguageTool.LanguageTool import LanguageTool

ADD_CONTENT_PREMISSIONS = 'Manage Portal'
lang_globals = globals()

PKG_NAME = 'PloneLanguageTool'

def initialize(context):
    ToolInit('Plone Language Tool',
             tools=(LanguageTool,),
             icon='tool.gif',
    ).initialize(context)
