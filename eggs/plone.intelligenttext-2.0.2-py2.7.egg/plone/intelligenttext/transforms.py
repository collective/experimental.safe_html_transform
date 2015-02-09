from htmlentitydefs import entitydefs
import re

class WebIntelligentToHtmlConverter(object):
    urlRegexp = re.compile(r'((?:ftp|https?)://(localhost|([12]?[0-9]{1,2}.){3}([12]?[0-9]{1,2})|(?:[a-z0-9](?:[-a-z0-9]*[a-z0-9])?\.)+(?:com|edu|biz|org|gov|int|info|mil|net|name|museum|coop|aero|[a-z][a-z]))\b(?::\d+)?(?:\/[^"\'<>()\[\]{}\s\x7f-\xff]*(?:[.,?]+[^"\'<>()\[\]{}\s\x7f-\xff]+)*)?)', re.I|re.S|re.U)
    emailRegexp = re.compile(r'["=]?(\b[A-Z0-9._%-]+@[A-Z0-9._%-]+\.[A-Z]{2,4}\b)', re.I|re.S|re.U)
    indentRegexp = re.compile(r'^(\s+)', re.M|re.U)

    def __init__(self, orig, tab_width=4):
        self.orig = orig
        self.tab_width = tab_width

    def __call__(self):
        text = self.orig
        if text is None:
            text = ''
        if not isinstance(text, unicode):
            text = unicode(text, 'utf-8', 'replace')

        # Do &amp; separately, else, it may replace an already-inserted & from
        # an entity with &amp;, so < becomes &lt; becomes &amp;lt;
        text = text.replace('&', '&amp;')
        # Make funny characters into html entity defs
        for entity, letter in entitydefs.items():
            if entity != 'amp':
                text = text.replace(
                    letter.decode('latin-1'), '&' + entity + ';')

        text = self.urlRegexp.subn(self.replaceURL, text)[0]
        text = self.emailRegexp.subn(self.replaceEmail, text)[0]
        text = self.indentRegexp.subn(self.indentWhitespace, text)[0]

        # convert windows line endings
        text = text.replace('\r\n', '\n')
        # Finally, make \n's into br's
        text = text.replace('\n', '<br />')

        text = text.encode('utf-8')

        return text

    @staticmethod
    def abbreviateUrl(url, max = 60, ellipsis = "[&hellip;]"):
        """very long urls are abbreviated to allow nicer layout
        """
        if len(url) < max:
            return url
        protocol = ""
        protocolend = url.find("//")
        if protocolend != -1:
            protocol = url[0:protocolend+2]
            url = url[protocolend+2:]
        list = url.split("/")
        if len(list) < 3 or len(list[0])+len(list[-1])>max:
            url = protocol + url
            center = (max-5)/2
            return url[:center] + ellipsis + url[-center:]

        return protocol + list[0] +"/" +ellipsis + "/" + list[-1]

    @classmethod
    def replaceURL(cls, match):
        """Replace hyperlinks with clickable <a> tags
        """
        url = match.groups()[0]
        linktext = cls.abbreviateUrl(url)
        # Also with <some link> we should only link to some link, not
        # including the brackets.
        end = ''
        # XXX Probably better to fix the regex above.  Maurits
        if url.endswith('&gt;'):
            url = url[:-len('&gt;')]
            linktext = linktext[:-len('&gt;')]
            end = '&gt;'

        # rel="nofollow" shall avoid spamming
        return '<a href="%s" rel="nofollow">%s</a>%s' % (url, linktext, end)

    @staticmethod
    def replaceEmail(match):
        """Replace email strings with mailto: links
        """
        url = match.groups()[0]
        # following unicode substitutions shall avoid email spam
        # crawlers to pickup email addresses
        url = url.replace('@', '&#0064;')
        return '<a href="&#0109;ailto&#0058;%s">%s</a>' % (url, url)

    def indentWhitespace(self, match):
        """Make leading whitespace on a line into &nbsp; to preserve indents
        """
        indent = match.groups()[0]
        indent = indent.replace(' ', '&nbsp;')
        return indent.replace('\t', '&nbsp;' * self.tab_width)

def convertWebIntelligentPlainTextToHtml(orig, tab_width=4):
    """Converts text/x-web-intelligent to text/html
    """
    try:
        # tab_width could be a string like '4'
        tab_width = int(tab_width)
    except ValueError:
        tab_width=4

    return WebIntelligentToHtmlConverter(orig, tab_width)()

def convertHtmlToWebIntelligentPlainText(orig):
    """Converts text/html to text/x-web-intelligent.
    """
    preRegex = re.compile(r'<\s*pre[^>]*>(.*?)<\s*/pre\s*>', re.I | re.S)

    tagWhitespaceRegex = re.compile(r'\s+((<[^>]+>)\s+)+')
    whitespaceRegex = re.compile(r'\s+')

    tdRegex = re.compile(r'<\s*(td)([^>])*>', re.I)
    breakRegex = re.compile(r'<\s*(br)\s*/?>', re.I)
    startBlockRegex = re.compile(r'<\s*(dt)[^>]*>', re.I)
    endBlockRegex = re.compile(r'<\s*/\s*(p|div|tr|ul|ol|dl)[^>]*>', re.I)
    indentBlockRegex = re.compile(r'<\s*(blockquote|dd)[^>]*>', re.I)
    listBlockRegex = re.compile(r'<\s*(li)[^>]*>', re.I)

    tagRegex = re.compile(r'<[^>]+>', re.I | re.M)

    # Save all <pre> sections and restore after other transforms
    preSections = {}

    def savePres(match):
        marker = '__pre_marker__%d__' % len(preSections)
        preSections[marker] = match.group(1)
        return marker
    if orig is None:
        orig = ''
    text = preRegex.sub(savePres, orig)

    def fixTagWhitespace(match):
        """Make whitespace-tag-whitespace into whitespace-tag.
        Repeat this in case there are directly nested tags.
        """
        # Remove any superfluous whitespace, but preserve one leading space
        return ' ' + whitespaceRegex.sub('', match.group(0))
    text = tagWhitespaceRegex.sub(fixTagWhitespace, text)

    # Make all whitespace into a single space
    text = whitespaceRegex.sub(' ', text)

    # Fix entities
    text = text.replace('&nbsp;', ' ')
    for entity, letter in entitydefs.items():
        # Do &lt; and &gt; later, else we may be creating what looks like
        # tags
        if entity != 'lt' and entity != 'gt':
            text = text.replace('&' + entity + ';', letter)

    # XXX: Remove <head>, <script>, <style> ?

    # Make tabs out of td's
    text = tdRegex.sub('\t', text)

    # Make br's and li's into newlines
    text = breakRegex.sub('\n', text)

    # Make the start of list blocks into paragraphs
    text = startBlockRegex.sub('\n\n', text)

    # Make the close of p's, div's and tr's into paragraphs
    text = endBlockRegex.sub('\n\n', text)

    # Make blockquotes and dd blocks indented
    text = indentBlockRegex.sub('\n\n  ', text)

    # Make list items indented and prefixed with -
    text = listBlockRegex.sub('\n\n  - ', text)

    # Remove other tags
    text = tagRegex.sub('', text)

    # Fix < and > entities
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')

    # Restore pres
    for marker, section in preSections.items():
        text = text.replace(marker, '\n\n' + section + '\n\n')

    return text
