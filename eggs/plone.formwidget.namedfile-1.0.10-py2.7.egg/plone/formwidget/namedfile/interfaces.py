from z3c.form.interfaces import IFileWidget
from zope import schema

class INamedFileWidget(IFileWidget):
    """A widget for a named file field
    """
    
    allow_nochange = schema.Bool(title=u"Allow user to keep existing data in lieu of uploading a file?")
    filename = schema.TextLine(title=u"Name of the underlying file", required=False)
    filename_encoded = schema.TextLine(title=u"Filename, URL-encoded", required=False)
    file_size = schema.Int(title=u"Size in kb", required=True, default=0)
    download_url = schema.URI(title=u"File download URL", required=False)
    
class INamedImageWidget(INamedFileWidget):
    """A widget for a named image field
    """
    
    width = schema.Int(title=u"Image width", min=0, required=False)
    height = schema.Int(title=u"Image height", min=0, required=False)
    
    thumb_width = schema.Int(title=u"Thumbnail image width", min=0, required=False)
    thumb_height = schema.Int(title=u"Thuimbnail image height", min=0, required=False)
    
    alt = schema.TextLine(title=u"Image alternative text", required=False)