from zope.interface import implements, Interface
from zope.schema import Tuple, List, TextLine
from zope.publisher.browser import TestRequest

from zope.formlib.widgets import ObjectWidget
from zope.formlib.interfaces import MissingInputError, WidgetInputError
from zope.formlib.widget import CustomWidgetFactory
from zope.formlib.tests.test_sequencewidget import SequenceWidgetTest as \
    BaseSequenceWidgetTest

from plone.app.form.widgets import SequenceWidget, TupleSequenceWidget, \
    ListSequenceWidget


class SequenceWidgetTest(BaseSequenceWidgetTest):
    """Documents and tests the tuple and list (sequence) widgets.

        >>> from zope.interface.verify import verifyClass
        >>> verifyClass(IInputWidget, TupleSequenceWidget)
        True
        >>> verifyClass(IInputWidget, ListSequenceWidget)
        True
    """

    _WidgetFactory = TupleSequenceWidget

    def setUpContent(self, desc=u'', title=u'Foo Title'):
        class ITestContent(Interface):
            foo = self._FieldFactory(
                    title=title,
                    description=desc,
                    )
        class TestObject(object):
            implements(ITestContent)
            foo = ('one', 'two')

        self.content = TestObject()
        self.field = ITestContent['foo'].bind(self.content)
        self.request = TestRequest(HTTP_ACCEPT_LANGUAGE='pl')
        self.request.form['field.foo'] = u'Foo Value'
        self._widget = self._WidgetFactory(
            self.field, self.field.value_type, self.request)

    def test_customWidgetFactory(self):
        """Verify that the widget can be constructed via the CustomWidgetFactory
        (Issue #293)
        """

        value_type = TextLine(__name__=u'bar')
        self.field = List( __name__=u'foo', value_type=value_type )
        request = TestRequest()

        # set up the custom widget factory and verify that it works
        sw = CustomWidgetFactory(ListSequenceWidget)
        widget = sw(self.field, request)
        assert widget.subwidget is None
        assert widget.context.value_type is value_type

        # set up a variant that specifies the subwidget to use and verify it
        class PollOption(object) : pass
        ow = CustomWidgetFactory(ObjectWidget, PollOption)
        sw = CustomWidgetFactory(ListSequenceWidget, subwidget=ow)
        widget = sw(self.field, request)
        assert widget.subwidget is ow
        assert widget.context.value_type is value_type

    def test_subwidget(self):
        """This test verifies that the specified subwidget is not ignored.
        (Issue #293)
        """
        self.field = List(__name__=u'foo',
                          value_type=TextLine(__name__=u'bar'))
        request = TestRequest()

        class PollOption(object) : pass
        ow = CustomWidgetFactory(ObjectWidget, PollOption)
        widget = SequenceWidget(
            self.field, self.field.value_type, request, subwidget=ow)
        assert widget.subwidget is ow

    def test_list(self):
        self.field = List(
            __name__=u'foo',
            value_type=TextLine(__name__=u'bar'))
        request = TestRequest()
        widget = ListSequenceWidget(
            self.field, self.field.value_type, request)
        self.assertFalse(widget.hasInput())
        self.assertRaises(MissingInputError, widget.getInputValue)

        request = TestRequest(form={'field.foo.add': u'Add bar',
                                    'field.foo.count': u'0'})
        widget = ListSequenceWidget(
            self.field, self.field.value_type, request)
        self.assert_(widget.hasInput())
        self.assertRaises(WidgetInputError, widget.getInputValue)

        request = TestRequest(form={'field.foo.0.bar': u'Hello world!',
                                    'field.foo.count': u'1'})
        widget = ListSequenceWidget(
            self.field, self.field.value_type, request)
        self.assert_(widget.hasInput())
        self.assertEqual(widget.getInputValue(), [u'Hello world!'])

    def test_new(self):
        request = TestRequest()
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        self.assertFalse(widget.hasInput())
        self.assertRaises(MissingInputError, widget.getInputValue)
        check_list = ('input', 'name="field.foo.add"')
        self.verifyResult(widget(), check_list)

    def test_add(self):
        request = TestRequest(form={'field.foo.add': u'Add bar',
                                    'field.foo.count': u'0'})
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        self.assert_(widget.hasInput())
        self.assertRaises(WidgetInputError, widget.getInputValue)
        check_list = (
            'checkbox', 'field.foo.remove_0', 'input', 'field.foo.0.bar',
            'submit', 'submit', 'field.foo.add'
        )
        self.verifyResult(widget(), check_list, inorder=True)

    def test_request(self):
        request = TestRequest(form={'field.foo.0.bar': u'Hello world!',
                                    'field.foo.count': u'1'})
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        self.assert_(widget.hasInput())
        self.assertEqual(widget.getInputValue(), (u'Hello world!',))

    def test_existing(self):
        request = TestRequest()
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        widget.setRenderedValue((u'existing',))
        self.assertFalse(widget.hasInput())
        self.assertRaises(MissingInputError, widget.getInputValue)
        check_list = (
            'checkbox', 'field.foo.remove_0', 'input', 'field.foo.0.bar',
                'existing',
            'submit', 'submit', 'field.foo.add',
            'field.foo.count" value="1"',
        )
        self.verifyResult(widget(), check_list, inorder=True)
        widget.setRenderedValue((u'existing', u'second'))
        self.assertFalse(widget.hasInput())
        self.assertRaises(MissingInputError, widget.getInputValue)
        check_list = (
            'checkbox', 'field.foo.remove_0', 'input', 'field.foo.0.bar',
                'existing',
            'checkbox', 'field.foo.remove_1', 'input', 'field.foo.1.bar',
                'second',
            'submit', 'submit', 'field.foo.add',
            'field.foo.count" value="2"',
        )
        self.verifyResult(widget(), check_list, inorder=True)

    def test_remove(self):
        request = TestRequest(form={
            'field.foo.remove_0': u'1',
            'field.foo.0.bar': u'existing', 'field.foo.1.bar': u'second',
            'field.foo.remove': u'Remove selected items',
            'field.foo.count': u'2'})
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        widget.setRenderedValue((u'existing', u'second'))
        self.assertEqual(widget.getInputValue(), (u'second',))
        check_list = (
            'checkbox', 'field.foo.remove_0', 'input', 'field.foo.0.bar',
                'existing',
            'checkbox', 'field.foo.remove_1', 'input', 'field.foo.1.bar',
                'second',
            'submit', 'submit', 'field.foo.add',
            'field.foo.count" value="2"',
        )
        self.verifyResult(widget(), check_list, inorder=True)

    def test_min(self):
        request = TestRequest()
        self.field.min_length = 2
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        widget.setRenderedValue((u'existing',))
        self.assertRaises(MissingInputError, widget.getInputValue)
        check_list = (
            'input', 'field.foo.0.bar', 'existing',
            'input', 'field.foo.1.bar', 'value=""',
            'submit', 'field.foo.add'
        )
        s = widget()
        self.verifyResult(s, check_list, inorder=True)
        self.assertEqual(s.find('checkbox'), -1)

    def test_max(self):
        request = TestRequest()
        self.field.max_length = 1
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        widget.setRenderedValue((u'existing',))
        self.assertRaises(MissingInputError, widget.getInputValue)
        s = widget()
        self.assertEqual(s.find('field.foo.add'), -1)

    def test_anonymousfield(self):
        self.field = Tuple(__name__=u'foo', value_type=TextLine())
        request = TestRequest()
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        widget.setRenderedValue((u'existing',))
        s = widget()
        check_list = (
            'input', '"field.foo.0."', 'existing',
            'submit', 'submit', 'field.foo.add'
        )
        s = widget()
        self.verifyResult(s, check_list, inorder=True)

    def test_usererror(self):
        self.field = Tuple(__name__=u'foo',
                           value_type=TextLine(__name__='bar'))
        request = TestRequest(form={
            'field.foo.0.bar': u'', 'field.foo.1.bar': u'nonempty',
            'field.foo.count': u'2'})
        widget = TupleSequenceWidget(
            self.field, self.field.value_type, request)
        # Rendering a widget should not raise errors!
        widget()

        data = widget._generateSequence()
        self.assertEqual(data, [None, u'nonempty'])

    def doctest_widgeterrors(self):
        """Test that errors on subwidgets appear

            >>> field = Tuple(__name__=u'foo',
            ...               value_type=TextLine(__name__='bar'))
            >>> request = TestRequest(form={
            ...     'field.foo.0.bar': u'',
            ...     'field.foo.1.bar': u'nonempty',
            ...     'field.foo.count': u'2'})
            >>> widget = TupleSequenceWidget(field, field.value_type, request)

         If we render the widget, we see no errors:

            >>> print widget()
            <BLANKLINE>
            ...
            <tr>
              <td>
                 <input class="editcheck" type="checkbox"
                        name="field.foo.remove_0" />
              </td>
              <td>
                 <input class="textType" id="field.foo.0.bar"
                        name="field.foo.0.bar"
                        size="20" type="text" value=""  />
              </td>
            </tr>
            ...

         However, if we call getInputValue or hasValidInput, the
         errors on the widgets are preserved and displayed:

            >>> widget.hasValidInput()
            False

            >>> print widget()
            <BLANKLINE>
            ...
            <tr>
              <td>
                 <input class="editcheck" type="checkbox"
                        name="field.foo.remove_0" />
              </td>
              <td>
                 <span class="error">Required input is missing.</span>
                 <input class="textType" id="field.foo.0.bar"
                        name="field.foo.0.bar"
                        size="20" type="text" value=""  />
              </td>
            </tr>
            ...
        """

    def test_presensemarker(self):
        request = TestRequest()
        widget = SequenceWidget(self.field, self.field.value_type, request)
        self.assertEqual(widget._getPresenceMarker(2), '<input type="hidden" '
            'name="%s.count" value="2" originalValue="2" />' % widget.name)

        # now pass object w/o foo attribute and check if it won't break
        class ITestContent(Interface):
            foo = self._FieldFactory(
                    title=u'Foo',
                    description=u'Foo Field',
                    )
        class TestObject(object):
            implements(ITestContent)

        field = ITestContent['foo'].bind(TestObject())
        widget = SequenceWidget(field, field.value_type, request)
        self.assertEqual(widget._getPresenceMarker(1), '<input type="hidden" '
            'name="%s.count" value="1" />' % widget.name)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(SequenceWidgetTest))
    return suite
