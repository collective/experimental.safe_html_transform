# -*- coding: utf-8 -*-
# $Id: __init__.py 246084 2011-11-01 22:45:18Z glenfant $
"""aws.zope2zcmldoc"""

import logging
from zope.i18nmessageid import MessageFactory

LOG = logging.getLogger('aws.zope2zcmldoc')
awsZope2zcmldocMF = MessageFactory('aws.zope2zcmldoc')


def initialize(context):
    """Zope 2 Product like registrations
    """
    # Nothing at the moment, this is a place holder
    return
