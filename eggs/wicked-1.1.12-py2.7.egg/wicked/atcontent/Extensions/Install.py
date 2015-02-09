from cStringIO import StringIO
from Products.Archetypes.public import listTypes
from Products.Archetypes.Extensions.utils import installTypes
from wicked.atcontent import zope2
from wicked.at.Extensions.Install import install as installwickedat

def install(portal):
    out = StringIO()
    installwickedat(portal)
    installTypes(portal, out, listTypes(zope2.PROJECTNAME), zope2.PROJECTNAME)

