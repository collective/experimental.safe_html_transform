from Products.Marshall.handlers.atxml import registerNamespace

from adobens import AdobeXMP
from atns import Archetypes
from dcns import DublinCore
from cmfns import CMF

registerNamespace(DublinCore)
registerNamespace(AdobeXMP)
registerNamespace(Archetypes)
registerNamespace(CMF)

# we do cmf last because workflow might other get reset
# by a set id (manage_afterAdd hook) value change

