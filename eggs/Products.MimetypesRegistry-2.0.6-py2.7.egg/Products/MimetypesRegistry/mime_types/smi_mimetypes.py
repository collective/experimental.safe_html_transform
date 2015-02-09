import os
from stat import ST_MTIME
from cPickle import dump, load

from xml.sax import parse
from xml.sax.handler import ContentHandler

DIR = os.path.dirname(__file__)
SMI_NAME = "freedesktop.org.xml"
SMI_COMPILED_NAME = "freedesktop.org.xml.bin"
SMI_FILE = os.path.join(DIR, SMI_NAME)
SMI_COMPILED_FILE = os.path.join(DIR, SMI_COMPILED_NAME)

class SharedMimeInfoHandler(ContentHandler):

    current = None
    collect_comment = None

    def __init__(self):
        ContentHandler.__init__(self)
        self.mimes = []

    def startElement(self, name, attrs):
        if name in ('mime-type',):
            current = {'type': attrs['type'],
                       'comments': {},
                       'globs': [],
                       'aliases': []}
            self.mimes.append(current)
            self.current = current
            return
        if name in ('comment',):
            # If no lang, assume 'en'
            lang = attrs.get('xml:lang', 'en')
            if lang not in ('en',):
                # Ignore for now.
                return
            self.__comment_buffer = []
            self.__comment_lang = lang
            self.collect_comment = True
            return
        if name in ('glob',):
            globs = self.current['globs']
            globs.append(attrs['pattern'])
            return
        if name in ('alias',):
            aliases = self.current['aliases']
            aliases.append(attrs['type'])

    def endElement(self, name):
        if self.collect_comment and name in ('comment',):
            self.collect_comment = False
            lang = self.__comment_lang
            comment = u''.join(self.__comment_buffer)
            if not comment:
                comment = self.current['type']
            self.current['comments'][lang] = comment

    def characters(self, contents):
        if self.collect_comment:
            self.__comment_buffer.append(contents)


def parseSMIFile(infofile):
    handler = SharedMimeInfoHandler()
    parse(infofile, handler)
    return handler.mimes


def readSMIFile():
    """Reads a shared mime info XML file
    """
    mtime = 0
    try:
        mtime = os.stat(SMI_FILE)[ST_MTIME]
    except (IOError, OSError):
        pass

    if os.path.exists(SMI_COMPILED_FILE):
        # Update file?
        bin_mtime = 0
        try:
            bin_mtime = os.stat(SMI_COMPILED_FILE)[ST_MTIME]
        except (IOError, OSError):
            pass

        if mtime <= bin_mtime:
            # file is current
            result = None
            try:
                fd = open(SMI_COMPILED_FILE, 'rb')
                result = load(fd)
                fd.close()
            except (IOError, OSError, EOFError):
                pass

            if result:
                return result

    result = parseSMIFile(SMI_FILE)
    try:
        fd = open(SMI_COMPILED_FILE, 'wb')
        dump(result, fd, protocol=2)
        fd.close()
    except (IOError, OSError):
        pass

    return result

mimetypes = readSMIFile()

def initialize(registry):
    global mimetypes
    from Products.MimetypesRegistry.MimeTypeItem import MimeTypeItem
    from Products.MimetypesRegistry.common import MimeTypeException
    # Find things that are not in the specially registered mimetypes
    # and add them using some default policy, none of these will impl
    # iclassifier
    for res in mimetypes:
        mt = str(res['type'])
        mts = (mt,) + tuple(res['aliases'])

        # check the mime type
        try:
            mto =  registry.lookup(mt)
        except MimeTypeException:
            # malformed MIME type
            continue

        name = str(res['comments'].get(u'en', mt))

        # build a list of globs
        globs = []
        for glob in res['globs']:
            if registry.lookupGlob(glob):
                continue
            else:
                globs.append(glob)

        if mto:
            mto = mto[0]
            for glob in globs:
                if not glob in mto.globs:
                    mto.globs = list(mto.globs) + [glob]
                    registry.register_glob(glob, mto)
            for mt in mts:
                if not mt in mto.mimetypes:
                    mto.mimetypes = list(mto.mimetypes) + [mt]
                    registry.register_mimetype(mt, mto)
        else:
            isBin = mt.split('/', 1)[0] != "text"
            mti = MimeTypeItem(name, mimetypes=mts,
                               binary=isBin,
                               globs=globs)
            registry.register(mti)
