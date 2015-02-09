##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" CMFDefault content interfaces. """

from zope.interface import Interface

class IHTMLScrubber(Interface):
    """ Utility inteface for scrubbing user-supplied HTML.
    """
    def scrub(html):
        """ Return 'scrubbed' HTML.
        """

class IDocument(Interface):

    """ Textual content, in one of several formats.

    o Allowed formats include: structured text, HTML, plain text.
    """

    def CookedBody():
        """ Get the "cooked" (ready for presentation) form of the text.
        """

    def EditableBody():
        """ Get the "raw" (as edited) form of the text.
        """


class IMutableDocument(IDocument):

    """ Updatable form of IDocument.
    """

    def edit(text_format, text, file='', safety_belt=''):
        """ Update the document.

        o 'safety_belt', if passed, must match the value issued when the edit
        began.
        """


class INewsItem(IDocument):

    """A special document for news.
    """

    def edit(text, description=None, text_format=None):
        """Edit the News Item.
        """


class IMutableNewsItem(INewsItem):

    """Updatable form of INewsItem.
    """


class ILink(Interface):

    """ URL as content.
    """

    def getRemoteUrl():
        """ Return the URL to which the link points, as a string.
        """


class IMutableLink(ILink):

    """ Updatable form of ILink.
    """

    def edit(remote_url):
        """ Update the link.

        o 'remote_url' should be a URL in an RFC-compatible form.

        o If 'remote_url' is unparseable by urllib, raise ValueError.
        """


class IFavorite(ILink):

    """ Link to an internal object.
    """

    def getObject():
        """ Get the actual object that the Favorite is linking to.
        """


class IMutableFavorite(IFavorite, IMutableLink):

    """ Updatable form of IFavorite.
    """


class IFile(Interface):

    """ Binary content.
    """

    def get_size():
        """ Get the byte size of the file data.
        """

    def getContentType():
        """ Get the MIME type of the file data.
        """

    def __str__():
        """ Get the file data.
        """


class IMutableFile(IFile):

    """ Updatable form of IFile.
    """

    def manage_upload(file='', REQUEST=None):
        """ Replaces the current data of the object with file.
        """


class IImage(IFile):

    """ Image content.
    """

    def __str__():
        """ Get the default HTML 'img' tag for this image.
        """


class IMutableImage(IImage, IMutableFile):

    """ Updatable form of IImage.
    """
