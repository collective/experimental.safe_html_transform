from Acquisition import aq_base
from logging import getLogger
from logging import exception
from OFS.Image import Pdata
from plone.app.imaging.interfaces import (
    IImageScaling,
    IImageScaleFactory,
    IImagingSchema,
    IStableImageScale,
)
from plone.app.imaging.scale import ImageScale
from Products.Five import BrowserView
from zope.component.hooks import getSite
from zope.interface import alsoProvides
from zope.interface import implements
from zope.traversing.interfaces import ITraversable, TraversalError
from zope.publisher.interfaces import IPublishTraverse, NotFound
from ZODB.POSException import ConflictError


try:
    from plone.scale.storage import AnnotationStorage
    from plone.scale.scale import scaleImage
except ImportError:
    logger = getLogger('plone.app.imaging')
    logger.warn("Warning: no Python Imaging Libraries (PIL) found. "
                "Can't scale images.")


class ImageScaleFactory(object):
    """ adapter for image fields that allows generating scaled images """
    implements(IImageScaleFactory)

    def __init__(self, field):
        self.field = field
        imaging_schema = IImagingSchema(getSite())
        self.quality = getattr(imaging_schema, 'quality', None)

    def create(self, context, **parameters):
        value = self.field.get(context)
        data = getattr(aq_base(value), 'data', value)
        if isinstance(data, Pdata):
            data = str(data)
        if data:
            if 'quality' not in parameters and self.quality:
                parameters['quality'] = self.quality
            return scaleImage(data, **parameters)


class ImageScaling(BrowserView):
    """ view used for generating (and storing) image scales """
    implements(IImageScaling, ITraversable, IPublishTraverse)

    def publishTraverse(self, request, name):
        """ used for traversal via publisher, i.e. when using as a url """
        stack = request.get('TraversalRequestNameStack')
        if stack:
            # field and scale name were given...
            scale = stack.pop()
            image = self.scale(name, scale)             # this is aq-wrapped
        elif '.' in name:
            # we got a uid...
            uid, ext = name.rsplit('.', 1)
            storage = AnnotationStorage(self.context)
            info = storage.get(uid)
            image = None
            if info is not None:
                image = self.make(info).__of__(self.context)
                alsoProvides(image, IStableImageScale)
        else:
            # otherwise `name` must refer to a field...
            field = self.field(name)
            image = field.get(self.context)             # this is aq-wrapped
        if image is not None:
            return image
        raise NotFound(self, name, self.request)

    def traverse(self, name, furtherPath):
        """ used for path traversal, i.e. in zope page templates """
        if not furtherPath:
            field = self.context.getField(name)
            return field.get(self.context).tag()
        image = self.scale(name, furtherPath.pop())
        if image is not None:
            return image.tag()
        raise TraversalError(self, name)

    def make(self, info):
        """ instantiate an object implementing `IImageScale` """
        mimetype = info['mimetype']
        info['content_type'] = mimetype
        info['filename'] = self.context.getFilename()
        scale = ImageScale(info['uid'], **info)
        scale.size = len(scale.data)
        url = self.context.absolute_url()
        extension = mimetype.split('/')[-1]
        scale.url = '%s/@@images/%s.%s' % (url, info['uid'], extension)
        return scale

    def field(self, fieldname):
        """ return the field for a given name """
        if fieldname:
            return self.context.getField(fieldname)
        else:
            return self.context.getPrimaryField()

    def create(self, fieldname, direction='keep', **parameters):
        """ factory for image scales, see `IImageScaleStorage.scale` """
        field = self.field(fieldname)
        create = IImageScaleFactory(field).create
        try:
            return create(self.context, direction=direction, **parameters)
        except (ConflictError, KeyboardInterrupt):
            raise
        except Exception:
            if not field.swallowResizeExceptions:
                raise
            else:
                exception('could not scale "%r" of %r',
                          field, self.context.absolute_url())

    def modified(self):
        """ provide a callable to return the modification time of content
            items, so stored image scales can be invalidated """
        return self.context.modified().millis()

    def scale(self, fieldname=None, scale=None, height=None, width=None,
              **parameters):
        if scale is not None:
            available = self.getAvailableSizes(fieldname)
            if not scale in available:
                return None
            width, height = available[scale]

        if width is None and height is None:
            field = self.field(fieldname)
            return field.get(self.context)

        info = self.getInfo(
            fieldname=fieldname, scale=scale, height=height, width=width,
            **parameters
        )

        if info is not None:
            return self.make(info).__of__(self.context)

    def tag(self, fieldname=None, scale=None, height=None, width=None,
            css_class=None, direction='keep', **args):
        """
        Generate an HTML IMG tag for this image, with customization.
        Arguments to self.tag() can be any valid attributes of an IMG
        tag.  'src' will always be an absolute pathname, to prevent
        redundant downloading of images. Defaults are applied
        intelligently for 'height' and 'width'. If specified, the
        'scale' argument will be used to automatically adjust the
        output height and width values of the image tag.

        Since 'class' is a Python reserved word, it cannot be passed in
        directly in keyword arguments which is a problem if you are
        trying to use 'tag()' to include a CSS class. The tag() method
        will accept a 'css_class' argument that will be converted to
        'class' in the output tag to work around this.
        """

        if scale is not None:
            available = self.getAvailableSizes(fieldname)
            if not scale in available:
                return None
            width, height = available[scale]

        if width is None and height is None:
            field = self.field(fieldname)
            return field.tag(
                self.context, css_class=css_class, **args
            )

        info = self.getInfo(
            fieldname=fieldname, scale=scale,
            height=height, width=width,
            direction=direction,
        )

        width = info['width']
        height = info['height']
        mimetype = info['mimetype']
        extension = mimetype.split('/')[-1]

        url = self.context.absolute_url()
        src = '%s/@@images/%s.%s' % (url, info['uid'], extension)
        result = '<img src="%s"' % src

        if height:
            result = '%s height="%s"' % (result, height)

        if width:
            result = '%s width="%s"' % (result, width)

        if css_class is not None:
            result = '%s class="%s"' % (result, css_class)

        if args:
            for key, value in sorted(args.items()):
                if value:
                    result = '%s %s="%s"' % (result, key, value)

        return '%s />' % result

    def getAvailableSizes(self, fieldname=None):
        field = self.field(fieldname)
        return field.getAvailableSizes(self.context)

    def getImageSize(self, fieldname=None):
        field = self.field(fieldname)
        return field.getSize(self.context)

    def getInfo(self, fieldname=None, scale=None, height=None, width=None,
                **parameters):
        storage = AnnotationStorage(self.context, self.modified)
        return storage.scale(
            factory=self.create,
            fieldname=fieldname,
            height=height,
            width=width,
            **parameters)
