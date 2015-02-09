"""Initialize PasswordResetTool Product"""

from Products.CMFCore import utils
import PasswordResetTool
from zope.i18nmessageid import MessageFactory
passwordresetMessageFactory = MessageFactory('passwordresettool')

tools = ( PasswordResetTool.PasswordResetTool, )

def initialize(context):
    utils.ToolInit('Password Reset Tool',
                    tools = tools,
                    icon='tool.gif'
                    ).initialize( context )
