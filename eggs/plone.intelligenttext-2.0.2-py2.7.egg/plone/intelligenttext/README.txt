Intelligent text
================

Started by Martin Aspeli

This package contains a and a transform (for example for
portal_transforms in CMF) that is capable converting plain text into
HTML where line breaks and indentation is preserved, and web and email
addresses are made into clickable links.

Basic usage
-----------

The basic usage is turning intelligenttext into html:

    >>> from plone.intelligenttext.transforms import convertWebIntelligentPlainTextToHtml
    >>> text = 'Go to http://plone.org'
    >>> convertWebIntelligentPlainTextToHtml(text)
    'Go to <a href="http://plone.org" rel="nofollow">http://plone.org</a>'

And the other way around:

    >>> from plone.intelligenttext.transforms import convertHtmlToWebIntelligentPlainText
    >>> html = 'Go to <a href="http://plone.org" rel="nofollow">http://plone.org</a>'
    >>> convertHtmlToWebIntelligentPlainText(html)
    'Go to http://plone.org'


Intelligent text to html
------------------------

We can get a hyperlink.  We always add rel="nofollow" to make this
less interesting for spammers.

    >>> orig = "A test http://test.com"
    >>> convertWebIntelligentPlainTextToHtml(orig)
    'A test <a href="http://test.com" rel="nofollow">http://test.com</a>'

An email address should be clickable too:

    >>> orig = "A test test@test.com of mailto"
    >>> convertWebIntelligentPlainTextToHtml(orig)
    'A test <a href="&#0109;ailto&#0058;test&#0064;test.com">test&#0064;test.com</a> of mailto'

Some basic fallback would be nice:

    >>> convertWebIntelligentPlainTextToHtml(None)
    ''

Text, links and email addressed can be split over multiple lines.

    >>> orig = """A test
    ... URL: http://test.com End
    ... Mail: test@test.com End
    ... URL: http://foo.com End"""
    >>> convertWebIntelligentPlainTextToHtml(orig)
    'A test<br />URL: <a href="http://test.com" rel="nofollow">http://test.com</a> End<br />Mail: <a href="&#0109;ailto&#0058;test&#0064;test.com">test&#0064;test.com</a> End<br />URL: <a href="http://foo.com" rel="nofollow">http://foo.com</a> End'


Having the links at the end of the line should not have adverse effects.

    >>> orig = """A test
    ... URL: http://test.com
    ... Mail: test@test.com
    ... URL: http://foo.com"""
    >>> convertWebIntelligentPlainTextToHtml(orig)
    'A test<br />URL: <a href="http://test.com" rel="nofollow">http://test.com</a><br />Mail: <a href="&#0109;ailto&#0058;test&#0064;test.com">test&#0064;test.com</a><br />URL: <a href="http://foo.com" rel="nofollow">http://foo.com</a>'


Indentation should be preserved.

    >>> orig = """A test
    ...   URL: http://test.com
    ...     Mail: test@test.com
    ...       URL: http://foo.com"""
    >>> convertWebIntelligentPlainTextToHtml(orig)
    'A test<br />&nbsp;&nbsp;URL: <a href="http://test.com" rel="nofollow">http://test.com</a><br />&nbsp;&nbsp;&nbsp;&nbsp;Mail: <a href="&#0109;ailto&#0058;test&#0064;test.com">test&#0064;test.com</a><br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;URL: <a href="http://foo.com" rel="nofollow">http://foo.com</a>'
    >>> convertWebIntelligentPlainTextToHtml(orig).count('&nbsp;')
    12

HTML entities should be escaped.

    >>> orig = "Some & funny < characters"
    >>> convertWebIntelligentPlainTextToHtml(orig)
    'Some &amp; funny &lt; characters'

Accentuated characters, like in French, should be html escaped.

    >>> orig = "The French use é à ô ù à and ç."
    >>> convertWebIntelligentPlainTextToHtml(orig)
    'The French use &eacute; &agrave; &ocirc; &ugrave; &agrave; and &ccedil;.'

Links with ampersands in them should be handled correctly.

    >>> orig = "http://google.com/ask?question=everything&answer=42"
    >>> convertWebIntelligentPlainTextToHtml(orig)
    '<a href="http://google.com/ask?question=everything&amp;answer=42" rel="nofollow">http://google.com/ask?question=everything&amp;answer=42</a>'

We want to make sure that the text representation of long urls is not too long.

    >>> url0 = "http://verylonghost.longsubdomain.veryverylongdomain.com/index.html"
    >>> convertWebIntelligentPlainTextToHtml(url0)
    '<a href="http://verylonghost.longsubdomain.veryverylongdomain.com/index.html" rel="nofollow">http://verylonghost.longsub[&hellip;]rylongdomain.com/index.html</a>'
    >>> url1 = "http://www.example.com/longnamefortheeffectofsuch/thisisalsolong/hereisthelastrealroot/thisisanotherpage.html"
    >>> convertWebIntelligentPlainTextToHtml(url1)
    '<a href="http://www.example.com/longnamefortheeffectofsuch/thisisalsolong/hereisthelastrealroot/thisisanotherpage.html" rel="nofollow">http://www.example.com/[&hellip;]/thisisanotherpage.html</a>'
    >>> url2 = "https://secure.somehost.net/a/path/logout.do;jsessionid=0FB57237D0D20D377E74D29031090FF2.A11"
    >>> convertWebIntelligentPlainTextToHtml(url2)
    '<a href="https://secure.somehost.net/a/path/logout.do;jsessionid=0FB57237D0D20D377E74D29031090FF2.A11" rel="nofollow">https://secure.somehost.net[&hellip;]0D20D377E74D29031090FF2.A11</a>'

If there is a url in brackets, the link should not contain one of the brackets.

    >>> bracket_url = "<http://plone.org/products/poi/issues/155>"
    >>> convertWebIntelligentPlainTextToHtml(bracket_url)
    '&lt;<a href="http://plone.org/products/poi/issues/155" rel="nofollow">http://plone.org/products/poi/issues/155</a>&gt;'

Port numbers should be recognized as linkworthy.

    >>> url = "http://plone3.freeman-centre.ac.uk:8080/caldav"
    >>> convertWebIntelligentPlainTextToHtml(url)
    '<a href="http://plone3.freeman-centre.ac.uk:8080/caldav" rel="nofollow">http://plone3.freeman-centre.ac.uk:8080/caldav</a>'

localhost should be good.

    >>> url = "http://localhost:8080/"
    >>> convertWebIntelligentPlainTextToHtml(url)
    '<a href="http://localhost:8080/" rel="nofollow">http://localhost:8080/</a>'

Check ip numbers too while we are at it.

    >>> url = "http://127.0.0.1:8080/"
    >>> convertWebIntelligentPlainTextToHtml(url)
    '<a href="http://127.0.0.1:8080/" rel="nofollow">http://127.0.0.1:8080/</a>'
    >>> convertWebIntelligentPlainTextToHtml("http://255.255.255.255")
    '<a href="http://255.255.255.255" rel="nofollow">http://255.255.255.255</a>'
    >>> convertWebIntelligentPlainTextToHtml("http://0.0.0.0")
    '<a href="http://0.0.0.0" rel="nofollow">http://0.0.0.0</a>'


ftp is accepted.

    >>> convertWebIntelligentPlainTextToHtml("ftp://localhost")
    '<a href="ftp://localhost" rel="nofollow">ftp://localhost</a>'

https is accepted.

    >>> convertWebIntelligentPlainTextToHtml("https://localhost")
    '<a href="https://localhost" rel="nofollow">https://localhost</a>'

Unicode should be fine too.

    >>> text = u"Línk tö http://foo.ni"
    >>> convertWebIntelligentPlainTextToHtml(text)
    'L&Atilde;&shy;nk t&Atilde;&para; <a href="http://foo.ni" rel="nofollow">http://foo.ni</a>'

Leading whitespace is converted to non breaking spaces to preserve
indentation:

    >>> text = "Some text.\n    And some indentation."
    >>> convertWebIntelligentPlainTextToHtml(text)
    'Some text.<br />&nbsp;&nbsp;&nbsp;&nbsp;And some indentation.'

Leading tabs are converted to spaces.  The default is 4:

    >>> text = "Before the tab:\n\tand after the tab."
    >>> convertWebIntelligentPlainTextToHtml(text)
    'Before the tab:<br />&nbsp;&nbsp;&nbsp;&nbsp;and after the tab.'

You can specify a different tab width:

    >>> convertWebIntelligentPlainTextToHtml(text, tab_width=2)
    'Before the tab:<br />&nbsp;&nbsp;and after the tab.'

In case the tab width is not an integer, we try to convert it:

    >>> convertWebIntelligentPlainTextToHtml(text, tab_width='2')
    'Before the tab:<br />&nbsp;&nbsp;and after the tab.'

When that fails we fall back to 4 spaces:

    >>> convertWebIntelligentPlainTextToHtml(text, tab_width='1.5')
    'Before the tab:<br />&nbsp;&nbsp;&nbsp;&nbsp;and after the tab.'


Html to intelligent text
------------------------

We want the transform to work the other way around too.  For starters
this means that tags must be stripped.

    >>> orig = "Some <b>bold</b> text."
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'Some bold text.'

Some basic fallback would be nice:

    >>> convertHtmlToWebIntelligentPlainText(None)
    ''

Line breaks need to be handled.

    >>> orig = "Some<br/>broken<BR/>text<br />"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'Some\nbroken\ntext\n'

Starting blocks:

    >>> orig = "A block<dt>there</dt>"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'A block\n\nthere'

Ending blocks:

    >>> orig = "<p>Paragraph</p>Other stuff"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'Paragraph\n\nOther stuff'

Indenting blocks:

    >>> orig = "An<blockquote>Indented blockquote</blockquote>"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'An\n\n  Indented blockquote'

Lists:

    >>> orig = "A list<ul><li>Foo</li><li>Bar</li></ul>"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'A list\n\n  - Foo\n\n  - Bar\n\n'

Non breaking spaces:

    >>> orig = "Some space &nbsp;&nbsp;here"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'Some space   here'

Angles:

    >>> orig = "Watch &lt;this&gt; and &lsaquo;that&rsaquo;"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'Watch <this> and &#8249;that&#8250;'

Bullets:

    >>> orig = "A &bull; bullet"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'A &#8226; bullet'

Ampersands:

    >>> orig = "An &amp; ampersand"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'An & ampersand'

Entities:

    >>> orig = "A &mdash; dash"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'A &#8212; dash'

Pre formatted text:

    >>> orig = "A <pre>  pre\n  section</pre>"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'A \n\n  pre\n  section\n\n'

White space:
    >>> orig = "A \n\t spaceful, <b>  tag-filled</b>, <b> <i>  snippet\n</b></i>"
    >>> convertHtmlToWebIntelligentPlainText(orig)
    'A spaceful, tag-filled, snippet '
