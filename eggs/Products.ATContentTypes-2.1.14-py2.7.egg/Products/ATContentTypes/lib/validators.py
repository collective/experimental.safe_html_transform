from types import FileType
from Acquisition import aq_base

from Products.ATContentTypes.config import HAS_MX_TIDY
from Products.ATContentTypes.config import MX_TIDY_ENABLED
from Products.ATContentTypes.config import MX_TIDY_MIMETYPES
from Products.ATContentTypes.config import MX_TIDY_OPTIONS

from Products.validation.config import validation
from Products.validation.interfaces.IValidator import IValidator

import re
import encodings
import logging
logger = logging.getLogger('ATCT')

from ZPublisher.HTTPRequest import FileUpload

from zope.tal.htmltalparser import HTMLTALParser
from zope.tal.talgenerator import TALGenerator
from Products.PageTemplates.Expressions import getEngine
from zope.interface import implements

if HAS_MX_TIDY:
    from mx.Tidy import tidy as mx_tidy

# matches something like 'line 15 column 1 - Warning: missing ...'
RE_MATCH_WARNING = re.compile('^line (\d+) column (\d+) - Warning: (.*)$')
WARNING_LINE = 'line %d column %d - Warning: %s'

# matches something like 'line 15 column 1 - Error: missing ...'
RE_MATCH_ERROR = re.compile('^line (\d+) column (\d+) - Error: (.*)$')
ERROR_LINE = 'line %d column %d - Error: %s'

# the following regex is safe because *? matches the minimal text in the body tag
# and .* matches the maximum text between two body tags including other body tags
# if they exists
RE_BODY = re.compile('<body[^>]*?>(.*)</body>', re.DOTALL)

# get the encoding from an uploaded html-page
# e.g. <meta http-equiv="content-type" content="text/html; charset=ISO-8859-1">
# we get ISO-8859-1 into the second match, the rest into the first and third.
RE_GET_HTML_ENCODING = re.compile('(<meta.*?content-type.*?charset[\s]*=[\s]*)([^"]*?)("[^>]*?>)', re.S | re.I)

# subtract 11 line numbers from the warning/error
SUBTRACT_LINES = 11

validatorList = []


class TALValidator:
    """Validates a text to be valid TAL code

    """
    implements(IValidator)

    def __init__(self, name, title='', description=''):
        self.name = name
        self.title = title or name
        self.description = description

    def __call__(self, value, *args, **kw):
        gen = TALGenerator(getEngine(), xml=1, source_file=None)
        parser = HTMLTALParser(gen)
        try:
            parser.parseString(value)
        except Exception, err:
            return ("Validation Failed(%s): \n %s" % (self.name, err))
        return 1

validatorList.append(TALValidator('isTAL', title='', description=''))


class TidyHtmlValidator:
    """use mxTidy to check HTML

    Fail on errors and warnings
    Do not clean up the value
    """

    implements(IValidator)

    def __init__(self, name, title='', description=''):
        self.name = name
        self.title = title or name
        self.description = description

    def __call__(self, value, *args, **kw):
        if not (HAS_MX_TIDY and MX_TIDY_ENABLED):
            # no mxTidy installed
            return 1

        request = kw['REQUEST']
        field = kw['field']

        result = doTidy(value, field, request)
        if result is None:
            return 1

        nerrors, nwarnings, outputdata, errordata = result
        errors = nerrors + nwarnings

        if errors:
            return ("Validation Failed(%s): \n %s" % (self.name, errordata))
        else:
            return 1

validatorList.append(TidyHtmlValidator('isTidyHtml', title='', description=''))


class TidyHtmlWithCleanupValidator:
    """use mxTidy to check HTML

    Fail only on errors
    Clean up
    """

    implements(IValidator)

    def __init__(self, name, title='', description=''):
        self.name = name
        self.title = title or name
        self.description = description

    def __call__(self, value, *args, **kw):
        if not (HAS_MX_TIDY and MX_TIDY_ENABLED):
            # no mxTidy installed
            return 1

        request = kw['REQUEST']
        field = kw['field']

        result = doTidy(value, field, request, cleanup=1)
        if result is None:
            return 1

        nerrors, nwarnings, outputdata, errordata = result
        errors = nerrors

        # save the changed output in the request
        tidyAttribute = '%s_tidier_data' % field.getName()
        request[tidyAttribute] = outputdata

        if nwarnings:
            tidiedFields = list(request.get('tidiedFields', []))
            tidiedFields.append(field)
            request.set('tidiedFields', tidiedFields)

        if errors:
            return ("Validation Failed(%s): \n %s" % (self.name, errordata))
        else:
            return 1

validatorList.append(TidyHtmlWithCleanupValidator('isTidyHtmlWithCleanup', title='', description=''))


class NonEmptyFileValidator:
    """Fails on empty non-existant files
    """

    implements(IValidator)

    def __init__(self, name, title='', description=''):
        self.name = name
        self.title = title or name
        self.description = description

    def __call__(self, value, *args, **kwargs):
        instance = kwargs.get('instance', None)
        field = kwargs.get('field', None)

        # calculate size
        if isinstance(value, FileUpload) or type(value) is FileType \
          or hasattr(aq_base(value), 'tell'):
            value.seek(0, 2)  # eof
            size = value.tell()
            value.seek(0)
        else:
            try:
                size = len(value)
            except TypeError:
                size = 1

        if size == 0:
            return ("Validation failed: Uploaded file is empty")
        else:
            return True


validatorList.append(NonEmptyFileValidator('isNonEmptyFile', title='', description=''))

for validator in validatorList:
    # register the validators
    validation.register(validator)


def doTidy(value, field, request, cleanup=0):
    """Tidy the data in 'value' for the field in the current request

    Optional cleanup:
      * removes header/footer of the output data
      * Removes warnings from the error data

    Return None for 'nothing done'
    else return (nerrors, nwarnings, outputdata, errordata)
    """
    # we can't use the mimetype from the field because it's updated *after*
    # validation so we must get it from the request
    tf_name = '%s_text_format' % field.getName()
    text_format = getattr(request, tf_name, '')

    # MX_TIDY_MIMETYPES configuration option isn't empty
    # and the current text_format isn't in the list
    if MX_TIDY_MIMETYPES and text_format not in MX_TIDY_MIMETYPES:
        # do not filter this mime type
        return

    # it's a file upload
    if isinstance(value, FileUpload):
        # *mmh* ok it's a file upload but a file upload could destroy
        # the layout, too.
        # the validator can be called many times, we have to rewind
        # the FileUpload.
        value.seek(0)
        value = correctEncoding(value.read())
    else:
        value = wrapValueInHTML(value)

    result = mx_tidy(value, **MX_TIDY_OPTIONS)
    nerrors, nwarnings, outputdata, errordata = result

    # parse and change the error data
    errordata = parseErrorData(errordata, removeWarnings=cleanup)
    if cleanup and outputdata:
        # unwrap tidied output data
        outputdata = unwrapValueFromHTML(outputdata)

    return nerrors, nwarnings, outputdata, errordata


def wrapValueInHTML(value):
    """Wrap the data in a valid html construct to remove the missing title error
    """
    return """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title></title>
</head>
<body>
%s
</body>
</html>
""" % value


def unwrapValueFromHTML(value):
    """Remove the html stuff around the body
    """
    # get the body text
    result = RE_BODY.search(value)
    if result:
        body = result.group(1)
    else:
        raise ValueError('%s is not a html string' % value)

##    # remove 2 spaces from the beginning of each line
##    nlines = []
##    for line in body.split('\n'):
##        print line
##        if line[:2] == '  ':
##            nlines.append(line[2:])
##        else:
##            nlines.append(line)
##
##    return '\n'.join(nlines)
    return body


def correctEncoding(value):
    """correct the encoding of a html-page if we know it an mxTidy
       expects an other encoding
    """

    # we have nothing to do if mxTidy has no
    # fixed char_encoding
    if 'char_encoding' not in MX_TIDY_OPTIONS  \
           or (MX_TIDY_OPTIONS['char_encoding'] == 'raw'):
        return value

    match = RE_GET_HTML_ENCODING.search(value)
    if match:
        groups = match.groups()

        # lookup encodings in the pyhon encodings database
        # returns function-pointers that we can compare
        # need to normalize encodings a bit before
        html_encoding = groups[1].strip().lower()
        char_encoding = MX_TIDY_OPTIONS['char_encoding'].lower().strip()
        h_enc = encodings.search_function(html_encoding)
        c_enc = encodings.search_function(char_encoding)

        # one encoding is missing or they are equal
        if not (h_enc and c_enc) or  h_enc == c_enc:
            return value
        else:
            try:
                return unicode(value, html_encoding).encode(char_encoding)
            except:
                logger.info("Error correcting encoding from %s to %s" % (html_encoding, char_encoding))
    return value


def parseErrorData(data, removeWarnings=0):
    """Parse the error data to change some stuff
    """
    lines = data.split('\n')
    nlines = []
    for line in lines:
        # substract 11 lines from line
        error = RE_MATCH_ERROR.search(line)
        if error:
            # an error line
            lnum, cnum, text = error.groups()
            lnum = int(lnum) - SUBTRACT_LINES
            cnum = int(cnum)
            nlines.append(ERROR_LINE % (lnum, cnum, text))
        else:
            warning = RE_MATCH_WARNING.search(line)
            if warning and not removeWarnings:
                # a warning line and add warnings to output
                lnum, cnum, text = warning.groups()
                lnum = int(lnum) - SUBTRACT_LINES
                cnum = int(cnum)
                nlines.append(WARNING_LINE % (lnum, cnum, text))
            else:
                # something else
                nlines.append(line)
    return '\n'.join(nlines)
