# DocFinderTab 1.0.5
# (c) 2001-2011, Stefan H. Holek, stefan@epy.co.at
# http://pypi.python.org/pypi/Products.DocFinderTab
# License: ZPL
# Zope: 2.7-2.14

# Monkey patch wrapper around Dieter Maurer's DocFinder product
# http://www.dieter.handshake.de/pyprojects/zope/DocFinder.html
# Adds a Doc tab to all Zope objects

# Thanks to Dieter for his input on how to make this work with 
# PythonScripts and ExternalMethods, and for writing DocFinder 
# in the first place.

__doc__ = 'Add a Doc tab to all Zope objects'
__version__ = '1.0.5'

__refresh_module__ = 0

from AccessControl.Permission import registerPermissions
from permissions import ViewDocPermission, ViewDocDefaultRoles

def initialize(context):
    # Register the helpfile
    if hasattr(context, 'registerHelp'):
        context.registerHelp()
        context.registerHelpTitle('DocFinderTab')

    # Register our permission
    registerPermissions(((ViewDocPermission, (), ViewDocDefaultRoles),))

# Apply the inspect module patch
import patch_inspect

# Apply the DocFinderTab patch
import patch_zope

