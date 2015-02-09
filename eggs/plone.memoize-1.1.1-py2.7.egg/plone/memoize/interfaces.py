from zope.interface import Interface


class ICacheChooser(Interface):

    def __call__(fun_name):
        """Return a cache with a dict interface based on a dotted
        function name `fun_name`.

        May return None to indicate that there is no cache available.
        """


class IXHTMLCompressor(Interface):

    def compress(string):
        """Expects a valid XHTML Unicode string as input and returns a valid
        XHTML Unicode string.

        Examples of compression are removal of whitespace without a semantical
        meaning, lowercasing of tags and attribute names (which gzip
        compression can take advantage of) or removal of comments.
        """
