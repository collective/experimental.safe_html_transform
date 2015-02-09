from zope.interface import implements
from Products.Archetypes.Field import Image
from plone.app.imaging.interfaces import IImageScale


class ImageScale(Image):
    """ extend image class from `Archetypes.Field` by making sure the title
        gets always computed and not calling `_get_content_type` even though
        an explicit type has been passed """
    implements(IImageScale)

    def __init__(self, id, data, content_type, **kw):
        self.__name__ = id
        self.__dict__.update(kw)
        self.precondition = ''


        # `OFS.Image` has no proper support for file objects or iterators,
        # so we'll require `data` to be a string or a file-like object...
        if not isinstance(data, str):
            data = data.open('r').read()    # assume it's file-like
        self.update_data(data, content_type, size=len(data))

    def absolute_url(self):
        """ return the url for new-style scales, but fall back for others """
        if 'url' in self.__dict__:
            return self.url
        else:
            return super(ImageScale, self).absolute_url()

    def __call__(self, *args, **kw):
        """ calling the scale returns itself, so "nocall:" can be skipped """
        return self
