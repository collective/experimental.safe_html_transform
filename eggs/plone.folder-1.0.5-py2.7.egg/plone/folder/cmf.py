try:
    from Products.CMFCore.permissions import ModifyPortalContent
    from Products.CMFCore.PortalFolder import PortalFolderBase
    ModifyPortalContent, PortalFolderBase   # pyflakes is useful, but stupid!
except ImportError:
    # fake the required stuff if `CMFCore` isn't available...
    ModifyPortalContent = 'Modify portal content'
    class PortalFolderBase:
        def __init__(self, id, title='', description=''):
            pass
