# -*- coding: utf-8 -*-
"""
Add DynamicView FTI form (ZMI)
"""
# $Id$

from Products.CMFCore.browser.typeinfo import FactoryTypeInformationAddView
from Products.CMFDynamicViewFTI import DynamicViewTypeInformation

class DVFactoryTypeInformationAddView(FactoryTypeInformationAddView):
    """See FactoryTypeInformationAddView that does all the job"""

    klass = DynamicViewTypeInformation

    description = u'A dynamic view type information object defines a portal type.'

