"""If debug-mode=on, Monkey-patch the zpublisher_exception_hook to
call pdb.post_mortem on an error and enable import of pdb (and ipdb) in
unprotected code.
"""

import sys

import Globals
import AccessControl

if Globals.DevelopmentMode:
    sys.modules['Products.PDBDebugMode.Globals'] = Globals

    # Allow import of pdb in unprotected code
    AccessControl.allow_module('pdb')
    AccessControl.allow_module('ipdb')
