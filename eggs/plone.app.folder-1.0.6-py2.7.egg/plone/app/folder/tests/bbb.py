# helper module to ease setting up backward-compatibility tests for
# ATContentTypes and CMFPlone

from Testing.ZopeTestCase import installProduct, installPackage

# BBB Zope 2.12
try:
    from Zope2.App.zcml import load_config
    load_config # pyflakes
except ImportError:
    from Products.Five.zcml import load_config

from Products.Five import fiveconfigure

installProduct('Five', quiet=True)

fiveconfigure.debug_mode = True
import plone.app.folder
load_config('configure.zcml', plone.app.folder)
fiveconfigure.debug_mode = False

installPackage('plone.app.folder', quiet=True)
