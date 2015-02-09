from Products.CMFCore.utils import getToolByName

def export(self):
    ct = getToolByName(self, 'portal_catalog')
    ut = getToolByName(self, 'portal_url')
    mt = getToolByName(self, 'marshaller_registry')
    paths = []
    for pt in ('News Item', 'Link', 'Document', 'Image', 'File'):
        for r in ct(portal_type=pt):
            paths.append(ut.getRelativeUrl(r.getObject()))

    response = self.REQUEST.RESPONSE
    response.setHeader('content-type', 'application/octet-stream')
    response.setHeader('content-disposition', 'attachment; filename=export.zip')
    data = mt.export(self, paths).read()
    response.setHeader('content-length', len(data))
    return response.write(data)
