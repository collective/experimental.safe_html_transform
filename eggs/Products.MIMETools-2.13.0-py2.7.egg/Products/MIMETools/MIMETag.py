##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from cStringIO import StringIO
import mimetools

from DocumentTemplate.DT_Util import Eval
from DocumentTemplate.DT_Util import parse_params
from DocumentTemplate.DT_Util import ParseError
from DocumentTemplate.DT_Util import render_blocks
from DocumentTemplate.DT_String import String


class MIMEError(Exception):
    """MIME Tag Error"""

ENCODINGS = ('base64', 'quoted-printable', 'uuencode', 'x-uuencode', 'uue',
             'x-uue', '7bit')


class MIMETag(object):
    ''''''

    name='mime'
    blockContinuations=('boundary', )
    encode=None

    def __init__(self, blocks):
        self.sections = []
        self.multipart = 'mixed'

        for tname, args, section in blocks:
            if tname == 'mime':
                args = parse_params(args, type=None, type_expr=None,
                                    disposition=None, disposition_expr=None,
                                    encode=None, encode_expr=None, name=None,
                                    name_expr=None, filename=None,
                                    filename_expr=None, cid=None,
                                    cid_expr=None, charset=None,
                                    charset_expr=None, skip_expr=None,
                                    multipart=None)
                self.multipart = args.get('multipart', 'mixed')
            else:
                args = parse_params(args, type=None, type_expr=None,
                                    disposition=None, disposition_expr=None,
                                    encode=None, encode_expr=None, name=None,
                                    name_expr=None, filename=None,
                                    filename_expr=None, cid=None,
                                    cid_expr=None, charset=None,
                                    charset_expr=None, skip_expr=None)

            if 'type_expr' in args:
                if 'type' in args:
                    raise ParseError(_tm('type and type_expr given', 'mime'))
                args['type_expr'] = Eval(args['type_expr'])
            elif 'type' not in args:
                args['type']='application/octet-stream'

            if 'disposition_expr' in args:
                if 'disposition' in args:
                    raise ParseError(
                        _tm('disposition and disposition_expr given', 'mime'))
                args['disposition_expr'] = Eval(args['disposition_expr'])
            elif 'disposition' not in args:
                args['disposition'] = ''

            if 'encode_expr' in args:
                if 'encode' in args:
                    raise ParseError(
                        _tm('encode and encode_expr given', 'mime'))
                args['encode_expr'] = Eval(args['encode_expr'])
            elif 'encode' not in args:
                args['encode'] = 'base64'

            if 'name_expr' in args:
                if 'name' in args:
                    raise ParseError(_tm('name and name_expr given', 'mime'))
                args['name_expr'] = Eval(args['name_expr'])
            elif 'name' not in args:
                args['name'] = ''

            if 'filename_expr' in args:
                if 'filename' in args:
                    raise ParseError(
                        _tm('filename and filename_expr given', 'mime'))
                args['filename_expr'] = Eval(args['filename_expr'])
            elif 'filename' not in args:
                args['filename'] = ''

            if 'cid_expr' in args:
                if 'cid' in args:
                    raise ParseError(_tm('cid and cid_expr given', 'mime'))
                args['cid_expr'] = Eval(args['cid_expr'])
            elif 'cid' not in args:
                args['cid'] = ''

            if 'charset_expr' in args:
                if 'charset' in args:
                    raise ParseError(
                        _tm('charset and charset_expr given', 'mime'))
                args['charset_expr'] = Eval(args['charset_expr'])
            elif 'charset' not in args:
                args['charset'] = ''

            if 'skip_expr' in args:
                args['skip_expr'] = Eval(args['skip_expr'])

            if args['encode'] not in ENCODINGS:
                raise MIMEError('An unsupported encoding was specified in tag')

            self.sections.append((args, section.blocks))

    def render(self, md):
        from MimeWriter import MimeWriter # deprecated since Python 2.3!
        IO = StringIO()
        IO.write("Mime-Version: 1.0\n")
        mw = MimeWriter(IO)
        outer = mw.startmultipartbody(self.multipart)

        last = None
        for x in self.sections:
            a, b = x
            if 'skip_expr' in a and a['skip_expr'].eval(md):
                continue

            inner = mw.nextpart()

            if 'type_expr' in a:
                t = a['type_expr'].eval(md)
            else:
                t = a['type']

            if 'disposition_expr' in a:
                d = a['disposition_expr'].eval(md)
            else:
                d = a['disposition']

            if 'encode_expr' in a:
                e = a['encode_expr'].eval(md)
            else:
                e = a['encode']

            if 'name_expr' in a:
                n = a['name_expr'].eval(md)
            else:
                n = a['name']

            if 'filename_expr' in a:
                f = a['filename_expr'].eval(md)
            else:
                f = a['filename']

            if 'cid_expr' in a:
                cid = a['cid_expr'].eval(md)
            else:
                cid = a['cid']

            if 'charset_expr' in a:
                charset = a['charset_expr'].eval(md)
            else:
                charset = a['charset']

            if d:
                if f:
                    inner.addheader('Content-Disposition',
                                    '%s;\n filename="%s"' % (d, f))
                else:
                    inner.addheader('Content-Disposition', d)

            inner.addheader('Content-Transfer-Encoding', e)

            if cid:
                inner.addheader('Content-ID', '<%s>' % cid)

            if n:
                plist = [('name', n)]
            else:
                plist = []

            if t.startswith('text/'):
                plist.append(('charset', charset or 'us-ascii'))

            innerfile = inner.startbody(t, plist, 1)

            output = StringIO()
            if e == '7bit':
                innerfile.write(render_blocks(b, md))
            else:
                mimetools.encode(StringIO(render_blocks(b, md)),
                                 output, e)
                output.seek(0)
                innerfile.write(output.read())

            last = x

        # XXX what if self.sections is empty ??? does it matter that
        # mw.lastpart() is called right after mw.startmultipartbody() ?
        if last is not None and last is self.sections[-1]:
            mw.lastpart()

        outer.seek(0)
        return outer.read()

    __call__ = render


String.commands['mime'] = MIMETag
