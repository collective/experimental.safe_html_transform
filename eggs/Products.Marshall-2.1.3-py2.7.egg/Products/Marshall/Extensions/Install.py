"""
$Id$
"""

from cStringIO import StringIO
from Products.CMFCore.utils import getToolByName
from Products.Marshall import registry
from Products.Marshall.config import TOOL_ID as tool_id

add_registry = registry.manage_addRegistry

def install_tool(self, out):
    tool = getToolByName(self, tool_id, None)
    if tool is not None:
        out.write('Registry was already installed.\n')
        return
    add_registry(self)
    out.write('Registry installed sucessfully.\n')

def install(self, out=None):
    if out is None:
        out = StringIO()

    install_tool(self, out)

    return out.getvalue()
