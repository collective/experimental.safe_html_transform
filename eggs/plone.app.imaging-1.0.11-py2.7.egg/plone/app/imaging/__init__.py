from Products.CMFCore.permissions import setDefaultRoles
try:
	import Products.ATContentTypes
except ImportError:
	HAS_ATCT = False
else:
	HAS_ATCT = True
	from plone.app.imaging.monkey import patchImageField
	from plone.app.imaging.monkey import patchSchemas

setDefaultRoles('Plone Site Setup: Imaging', ('Manager', 'Site Administrator'))

def initialize(context):
	if HAS_ATCT:
	    patchImageField()       # patch ImageField's `getAvailableSizes` method
	    patchSchemas()          # patch ATCT schemas with `sizes` attribute
