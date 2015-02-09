from Products.validation.interfaces.IValidator import IValidator
from zope.interface import implements
from Products.validation.i18n import PloneMessageFactory as _
from Products.validation.i18n import recursiveTranslate
from Products.validation.i18n import safe_unicode
import re
from types import StringType

def ignoreRE(value, expression):
    ignore = re.compile(expression)
    return ignore.sub('', value)

class RegexValidator:
    implements(IValidator)

    def __init__(self, name, *args, **kw):
        self.name = name
        self.title = kw.get('title', name)
        self.description = kw.get('description', '')
        self.errmsg = kw.get('errmsg', 'fails tests of %s' % name)
        self.regex_strings = args
        self.ignore = kw.get('ignore', None)
        self.regex = []
        self.compileRegex()

    def compileRegex(self):
        for r in self.regex_strings:
            self.regex.append(re.compile(r))

    def __getstate__(self):
        """Because copy.deepcopy and pickle.dump cannot pickle a regex pattern
        I'm using the getstate/setstate hooks to set self.regex to []
        """
        d = self.__dict__.copy()
        d['regex'] = []
        return d

    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.compileRegex()

    def __call__(self, value, *args, **kwargs):
        if type(value) != StringType:
            msg =  _(u"Validation failed($name): $value of type $type, expected 'string'",
                     mapping = {
                        'name' : safe_unicode(self.name),
                        'value': safe_unicode(value),
                        'type' : safe_unicode(type(value))
                        })
            return recursiveTranslate(msg, **kwargs)

        ignore = kwargs.get('ignore', None)
        if ignore:
            value = ignoreRE(value, ignore)
        elif self.ignore:
            value = ignoreRE(value, self.ignore)


        for r in self.regex:
            m = r.match(value)
            if not m:
                msg =  _(u"Validation failed($name): '$value' $errmsg",
                         mapping={
                            'name' : safe_unicode(self.name),
                            'value': safe_unicode(value),
                            'errmsg' : safe_unicode(self.errmsg)
                            })

                return recursiveTranslate(msg, **kwargs)
        return 1
