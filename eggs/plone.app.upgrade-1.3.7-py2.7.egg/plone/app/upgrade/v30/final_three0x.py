from Products.CMFCore.utils import getToolByName
from Products.CMFEditions.StandardModifiers import install

from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile


def final_three01(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v30:3.0final-3.0.1')


def three01_three02(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v30:3.0.1-3.0.2')


def three03_three04(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v30:3.0.3-3.0.4')


def installNewModifiers(context):
    modifiers = getToolByName(context, 'portal_modifier', None)
    if modifiers is not None:
        install(modifiers)
        logger.info('Added new CMFEditions modifiers.')
