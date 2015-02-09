"""
The following examples would all be added into the viewlets.xml file.

Re-order viewlets::

    <order manager="plone.portaltop" skinname="Plone
    Default">
      <viewlet name="plone.header"/>
      <viewlet name="plone.personal_bar"/>
    </order>

Move a viewlet using insert-before and insert-after (this will only affect
the skinname that is specified, in this case 'My Custom Theme')::

    <order manager="plone.portalheader" skinname="My
    Custom Theme" based-on="Plone Default">
      <viewlet name="plone.global_sections" insertbefore="*"/>
      <viewlet name="plone.site_actions" insertafter="plone.searchbox"/>
    </order>

Hide a viewlet (here we hide the colophon for 'My Custom Theme')::

    <hidden manager="plone.portalfooter" skinname="My
    Custom Theme">
      <viewlet name="plone.colophon"/>
    </hidden>

Unhide a specific viewlet using the remove attribute::

    <hidden manager="plone.portalfooter" skinname="My
    Custom Theme">
      <viewlet name="plone.colophon" remove="True"/>
    </hidden>

Unhide all viewlets for a given manager using the purge attribute::

    <hidden manager="plone.portalfooter" skinname="My
    Custom Theme" purge="True"/>

Hide a viewlet for all skins::

    <hidden manager="plone.portalfooter" skinname="*">
      <viewlet name="plone.colophon"/>
    </hidden>

Pro Tip: Using skinname="*" currently only works if the manager has
already been registered in each skin (see Plone Trac ticket #7166)

.. These docs are used in c.developermanual
.. original content from http://www.sixfeetup.com/company/technologies/plone-content-management-new/quick-reference-cards/swag/swag-images-files/generic_setup.pdf

"""

import os

from zope.component import getUtility, queryUtility, queryMultiAdapter
from zope.schema.interfaces import IVocabularyFactory
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.utils import XMLAdapterBase
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage


def importViewletSettingsStorage(context):
    """Import viewlet settings."""
    logger = context.getLogger('plone.app.viewletmanager')

    body = context.readDataFile('viewlets.xml')
    if body is None:
        return

    storage = getUtility(IViewletSettingsStorage)

    importer = queryMultiAdapter((storage, context), IBody)
    if importer is None:
        logger.warning("Import adapter missing.")
        return

    # set filename on importer so that syntax errors can be reported properly
    try:
        subdir = context._profile_path
    except AttributeError:
        subdir = ''
    importer.filename = os.path.join(subdir, 'viewlets.xml')

    importer.body = body
    logger.info("Imported.")


def exportViewletSettingsStorage(context):
    """Export viewlet settings."""
    logger = context.getLogger('plone.app.viewletmanager')

    storage = queryUtility(IViewletSettingsStorage)
    if storage is None:
        return

    exporter = queryMultiAdapter((storage, context), IBody)
    if exporter is None:
        logger.warning("Export adapter missing.")
        return

    context.writeDataFile('viewlets.xml', exporter.body, exporter.mime_type)
    logger.info("Exported.")


class ViewletSettingsStorageNodeAdapter(XMLAdapterBase):
    __used_for__ = IViewletSettingsStorage

    def __init__(self, context, environ):
        super(ViewletSettingsStorageNodeAdapter, self).__init__(context, environ)

        self.skins = [skin.token for skin in getUtility(IVocabularyFactory,
                         'plone.app.vocabularies.Skins')(self.context)]

    def _exportNode(self):
        """
        Export the object as a DOM node.
        """
        output = self._doc.createElement('object')
        for nodename in ('order', 'hidden'):
            skins = getattr(self.context, '_'+nodename)
            for skin in skins:
                for name in skins[skin]:
                    node = self._doc.createElement(nodename)
                    node.setAttribute('skinname', skin)
                    node.setAttribute('manager', name)
                    for viewlet in skins[skin][name]:
                        child = self._doc.createElement('viewlet')
                        child.setAttribute('name', viewlet)
                        node.appendChild(child)
                    output.appendChild(node)
        return output

    def _importNode(self, node):
        """
        Import the object from the DOM node.
        """
        storage = self.context
        purge = self.environ.shouldPurge()
        if node.getAttribute('purge'):
            purge = self._convertToBoolean(node.getAttribute('purge'))
        if purge:
            self._purgeViewletSettings()
        for child in node.childNodes:
            nodename = child.nodeName
            if nodename not in ('order', 'hidden'):
                continue
            purgeChild = False
            if child.getAttribute('purge'):
                purgeChild = self._convertToBoolean(
                                                  child.getAttribute('purge'))
            skinname = child.getAttribute('skinname')
            manager = child.getAttribute('manager')
            skins = getattr(storage, '_'+nodename)

            all_skins = tuple(set(storage._hidden.keys() + \
                                  storage._order.keys() + \
                                  self.skins))

            if skinname == '*':
                for skinname in all_skins:
                    values = []
                    if skinname in skins and not purgeChild:
                        values = list(skins[skinname].get(manager, []))
                    values = self._computeValues(values, child)
                    if nodename == 'order':
                        storage.setOrder(manager, skinname, tuple(values))
                    elif nodename == 'hidden':
                        storage.setHidden(manager, skinname, tuple(values))

            else:
                values = []
                if skinname in skins and not purgeChild:
                    values = list(skins[skinname].get(manager, []))
                basename = child.getAttribute('based-on')
                if basename in skins:
                    oldvalues = values
                    values = list(skins[basename].get(manager, []))
                    for value in oldvalues:
                        if value not in values:
                            viewlet = self._doc.createElement('viewlet')
                            viewlet.setAttribute('name', value)
                            if oldvalues.index(value) == 0:
                                viewlet.setAttribute('insert-before', '*')
                            else:
                                pos = oldvalues[oldvalues.index(value)-1]
                                viewlet.setAttribute('insert-after', pos)
                            child.appendChild(viewlet)
                values = self._computeValues(values, child)
                if nodename == 'order':
                    storage.setOrder(manager, skinname, tuple(values))
                elif nodename == 'hidden':
                    storage.setHidden(manager, skinname, tuple(values))

                if child.hasAttribute('make_default'):
                    make_default = self._convertToBoolean(
                                        child.getAttribute('make_default'))
                    if make_default == True:
                        storage.setDefault(manager, skinname)

    def _purgeViewletSettings(self):
        storage = self.context
        for key in storage._order:
            storage._order[key].clear()
        for key in storage._hidden:
            storage._hidden[key].clear()

    def _computeValues(self, values, node):
        for child in node.childNodes:
            if child.nodeName != 'viewlet':
                continue
            viewlet_name = child.getAttribute('name')
            if viewlet_name in values:
                values.remove(viewlet_name)

            if child.hasAttribute('insert-before'):
                insert_before = child.getAttribute('insert-before')
                if insert_before == '*':
                    values.insert(0, viewlet_name)
                    continue
                else:
                    try:
                        index = values.index(insert_before)
                        values.insert(index, viewlet_name)
                        continue
                    except ValueError:
                        pass
            elif child.hasAttribute('insert-after'):
                insert_after = child.getAttribute('insert-after')
                if insert_after == '*':
                    pass
                else:
                    try:
                        index = values.index(insert_after)
                        values.insert(index+1, viewlet_name)
                        continue
                    except ValueError:
                        pass

            if not child.hasAttribute('remove'):
                values.append(viewlet_name)

        return values
