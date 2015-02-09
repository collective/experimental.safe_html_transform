from z3c.form.converter import BaseDataConverter
from zope.schema.interfaces import IList
from plone.formwidget.querystring.interfaces import IQueryStringWidget
import zope.component


class AttributeDict(dict):
    """Dictionary which provides contents as attributes"""

    def __getattr__(self, key):
        return self[key]


class QueryStringConverter(BaseDataConverter):
    """Converts values for use with QueryStringWidget (make z3c.form happy)"""
    zope.component.adapts(IList, IQueryStringWidget)

    def toWidgetValue(self, value):
        """Converts given value for use in the widget"""

        if value is self.field.missing_value:
            return value
        else:
            data = []
            for dict_ in value:
                new_dict = AttributeDict()
                for key, value in dict_.items():
                    if isinstance(value, list):
                        new_dict[key.encode('utf-8')] = \
                        [x.encode('utf-8') for x in value]
                    else:
                        new_dict[key.encode('utf-8')] = value.encode('utf-8')
                data.append(new_dict)
            return data

    def toFieldValue(self, value):
        """Converts value for use in the field"""
        if value is self.field.missing_value:
            return value
        else:
            data = []
            for dict_ in value:
                new_dict = {}
                for key, value in dict_.items():
                    if isinstance(value, list):
                        new_dict[key.decode('utf-8')] = \
                        [x.decode('utf-8') for x in value]
                    else:
                        new_dict[key.decode('utf-8')] = value.decode('utf-8')
                data.append(new_dict)
            return data
