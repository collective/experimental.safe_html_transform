from zope import interface

class ITemplateManager(interface.Interface):
    def registerDirectory(directory):
        pass

    def unregisterDirectory(directory):
        pass

    
