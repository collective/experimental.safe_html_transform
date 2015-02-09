# -*- coding: utf-8 -*-

# $Id$

from Products.CMFCore import utils as cmf_utils
from Products.CMFDynamicViewFTI.fti import DynamicViewTypeInformation

def initialize(context):
    # (DynamicViewTypeInformation factory is created from ZCML)
    cmf_utils.registerIcon(DynamicViewTypeInformation, 'images/typeinfo.gif', globals())
    return
