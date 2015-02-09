# -*- coding: utf-8 -*-
# $Id: interfaces.py 84486 2009-04-17 12:56:00Z jfroche $
"""Public interfaces"""
from zope.interface import Interface
from zope.schema import Dict


class IMonkeyPatchEvent(Interface):
    """Monkey patch applied event"""

    patch_info = Dict(
        title=u"Misc information about the patch",
        description=u"""A mapping about the patch with following keys:
        * 'description': A text that describes the monkey patch
        * 'zcml_info': A text about the ZCML portion that made the patch
        * 'original': Dotted name of the original method/function.
        * 'replacement': Dotted name of the new function
        """)
