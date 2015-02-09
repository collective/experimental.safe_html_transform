from zope.interface import Interface


class IRuleElementExportImportHandler(Interface):
    """An adapter which is used to export/import GenericSetup configuration
    for a particular content rule element (condition or action)
    """

    def import_element(node):
        """Set the properties on the given element, based on the given
        element schema interface. The node is the <condition /> or <action />
        root node. Settings are expected to be found in children of the node.
        """

    def export_element(doc, node):
        """Export the properties of the given element with the given
        element schema interface and append them to the given root node.
        Use the doc object to create new nodes.
        """
