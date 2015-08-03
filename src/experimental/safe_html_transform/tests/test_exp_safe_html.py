# -*- coding: utf-8 -*-
import unittest2 as unittest
from Products.PortalTransforms.data import datastream


class safe_htmlUnitTest(unittest.TestCase):

    def setUp(self):
        self.transform = self._makeOne()

    def _getTargetClass(self):
	    from experimental.safe_html_transform.transforms.exp_safe_html import \
                SafeHTML
            return SafeHTML

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_empty(self):
        orig = ""
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(orig, data)._data, "")

    # Valid Elements
    def test_keep_h2_headlines(self):
        orig = "<h2>Headlines are good!</h2>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(orig, data)._data,
                         "<h2>Headlines are good!</h2>")

    def test_keep_paragraphs(self):
        html = "<p>paragraphs are good!</p>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         "<p>paragraphs are good!</p>")

    def test_keep_spans(self):
        html = "<span>spans are good!</span>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         "<span>spans are good!</span>")

    def test_keep_span_style_attribue(self):
        html = '<span style="color: red;">spans are good!</span>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<span style="color: red;">spans are good!</span>')

    def test_keep_italic(self):
        html = "<i>italic is nice!</i>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         "<i>italic is nice!</i>")

    def test_keep_strong(self):
        html = "<strong>strong is good!</strong>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         "<strong>strong is good!</strong>")

    def test_keep_bold(self):
        html = "<b>boldness is also good</b>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         "<b>boldness is also good</b>")

    def test_keep_emphasis(self):
        html = "<em>emphasis is good!</em>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         "<em>emphasis is good!</em>")

    def test_keep_sup(self):
        html = "<sup>sup is good!</sup>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         "<sup>sup is good!</sup>")

    def test_keep_sub(self):
        html = "<sub>sub is good!</sub>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         "<sub>sub is good!</sub>")

    def test_keep_links(self):
        html = '<a href="http://www.xxx.de">xxx rules!</a>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<a href="http://www.xxx.de">xxx rules!</a>')

    def test_keep_iframes(self):
        html = '<iframe src="http://www.xxx.de">xxx IFrame</iframe>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<iframe src="http://www.xxx.de">xxx IFrame</iframe>'
                         )

    def test_keep_images(self):
        html = '<img src="logo.png"/>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<img src="logo.png"/>'
                         )

    def test_keep_images_with_alt_attribute(self):
        html = '<img src="logo.png" alt="logo"/>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<img src="logo.png" alt="logo"/>'
                         )

    def test_keep_images_with_logo_attribute(self):
        html = '<img src="logo.png" alt="logo"/>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<img src="logo.png" alt="logo"/>'
                         )

    def test_keep_images_with_title_attribute(self):
        html = '<img src="logo.png" title="logo"/>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<img src="logo.png" title="logo"/>'
                         )

    def test_keep_images_with_width_attribute(self):
        html = '<img src="logo.png" width="100"/>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<img src="logo.png" width="100"/>'
                         )

    def test_keep_images_with_height_attribute(self):
        html = '<img src="logo.png" height="100"/>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<img src="logo.png" height="100"/>'
                         )

    def test_keep_images_with_align_attribute(self):
        html = '<img src="logo.png" align="center"/>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<img src="logo.png" align="center"/>'
                         )

    # Ignores
    def test_ignore_headlines_other_than_h1_or_h2(self):
        html = '<h3>foo</h3><h4>bar</h4><h5>baz</h5><h6>boz</h6><p>Keep me</p>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<p>foo</p><p>bar</p><p>baz</p><p>boz</p><p>Keep me</p>')

    def test_ignore_top_level_elements(self):
        html = '<html><p>Keep me</p></html>'
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<p>Keep me</p>')

    def test_multiple_elements(self):
        html = "<p>foo</p><p>bar</p>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         "<p>foo</p><p>bar</p>")

    def test_transform_brackets(self):
        html = "<p>>>>foo<<<</p>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         "<p>&gt;&gt;&gt;foo</p>")
    # XXX: "<" should be transformed into "&lt;" and not ignored. Since
    # these are filtered by XSLT this is hard to debug/fix.

    # Nested
    def test_nested_elements(self):
        html = "<div>foo<p>Keep me</p></div>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<p>foo</p><p>Keep me</p>')

    def test_strip_outer_whitespace(self):
        html = ' <p>Keep me</p> '
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data,
                         '<p>Keep me</p>')

    def test_html_single(self):
        html = "<html/>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data, "")

    def test_html_single_with_blank(self):
        html = "<html />"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data, "")

    def test_html_full_tag(self):
        html = "<html></html>"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data, "")

    def test_html_without_ptag(self):
        html = "<p>Keep me"
        data = datastream(self.transform.name())
        self.assertEqual(self.transform.convert(html, data)._data, "<p>Keep me</p>")
