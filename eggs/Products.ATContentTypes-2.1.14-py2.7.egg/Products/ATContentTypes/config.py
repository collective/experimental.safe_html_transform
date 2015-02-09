"""AT Content Types configuration file

DO NOT CHANGE THIS FILE!

Use ZConfig to configure ATCT
"""
__docformat__ = 'restructuredtext'

import pkg_resources
import os
from Products.ATContentTypes.configuration import zconf

## options for mx tidy
## read http://www.egenix.com/files/python/mxTidy.html for more informations
MX_TIDY_ENABLED = zconf.mxtidy.enable
MX_TIDY_OPTIONS = zconf.mxtidy.options

###############################################################################
## private options

PROJECTNAME = "ATContentTypes"
TOOLNAME = "portal_atct"
SKINS_DIR = 'skins'

ATCT_DIR = os.path.abspath(os.path.dirname(__file__))
WWW_DIR = os.path.join(ATCT_DIR, 'www')

GLOBALS = globals()

## swallow PIL exceptions when resizing the image?
SWALLOW_IMAGE_RESIZE_EXCEPTIONS = zconf.swallowImageResizeExceptions.enable

## mxTidy available?
try:
    # I am not sure, which pkg should contain mx.Tidy
    from mx import Tidy
except ImportError:
    HAS_MX_TIDY = False
else:
    HAS_MX_TIDY = True
    try:
        del Tidy
    except AttributeError:
        pass

## tidy only these document types
MX_TIDY_MIMETYPES = (
    'text/html',
     )

## ExternalStorage available?
try:
    pkg_resources.get_distribution('Products.ExternalStorage')
except pkg_resources.DistributionNotFound:
    HAS_EXT_STORAGE = False
else:
    HAS_EXT_STORAGE = True

## LinguaPlone addon?
try:
    pkg_resources.get_distribution('Products.LinguaPlone')
except pkg_resources.DistributionNotFound:
    HAS_LINGUA_PLONE = False
else:
    HAS_LINGUA_PLONE = True

try:
    # Won't use pkg_resources because of the packaging issue
    from PIL import Image
except ImportError:
    HAS_PIL = False
else:
    HAS_PIL = True


## workflow mapping for the installer
WORKFLOW_DEFAULT = '(Default)'
WORKFLOW_FOLDER = 'folder_workflow'
WORKFLOW_TOPIC = 'folder_workflow'
WORKFLOW_CRITERIA = ''

## icon map used for overwriting ATFile icons
ICONMAP = {'application/pdf': 'pdf_icon.png',
           'image': 'image_icon.png'}

MIME_ALIAS = {
    'plain': 'text/plain',
    'stx': 'text/structured',
    'html': 'text/html',
    'rest': 'text/x-rst',
    'text/stx': 'text/structured',
    'structured-text': 'text/structured',
    'restructuredtext': 'text/x-rst',
    'text/restructured': 'text/x-rst',
    }
