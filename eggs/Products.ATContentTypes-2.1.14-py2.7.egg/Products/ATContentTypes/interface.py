"""AT Content Types general interfaces

BBB: We used to have all interfaces specified in "interface". "interfaces" is
the conventional name, though.
"""

from Products.ATContentTypes.interfaces import *

# the following is a rather crude workaround for the failing imports
# seen in plone 4 when trying to import submodules from `ATCT.interface`:
#   >>> import Products.ATContentTypes.interface.interfaces
#   Traceback (most recent call last):
#     File "<stdin>", line 1, in <module>
#   ImportError: No module named interfaces
# apparently the modules imported from `interfaces` above are already
# somehow known to the interpreter and therefore not added to `sys.modules`
# again.  to work around we inject them manually...
from types import ModuleType
from sys import modules
for name, obj in globals().items():
    if type(obj) is ModuleType:
        modules['%s.%s' % (__name__, name)] = obj
